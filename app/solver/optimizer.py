import gurobipy as gp
from gurobipy import GRB
from pydantic import BaseModel

from .cards import Card, load_cards, CATEGORIES

HORIZON = 12  # months; annual fee deducted once


class OptimizationResult(BaseModel):
    wallet: list[str]
    allocation: dict[str, str]
    monthly_reward: float
    annual_fee: float
    net_annual_reward: float


def _dummy_card() -> Card:
    # Fallback card with no rewards and no minimums — ensures MILP is always feasible
    return Card(
        id="no_card",
        name="No Card",
        annual_fee=0.0,
        min_income=0.0,
        min_spend=0.0,
        overall_cap=999999.0,
        affiliate_url="",
        rates={k: 0.0 for k in CATEGORIES},
        category_caps={k: 999999.0 for k in CATEGORIES},
    )


def solve(
    monthly_spend: dict[str, float],
    income: float,
    max_cards: int = 3,
) -> OptimizationResult:
    # Filter cards by income eligibility; append dummy card for feasibility
    eligible = [c for c in load_cards() if income >= c.min_income] + [_dummy_card()]
    C = list(range(len(eligible)))
    K = CATEGORIES
    M = list(range(HORIZON))
    total_spend = sum(monthly_spend[k] for k in K)

    # Create Model
    model = gp.Model("card_optimizer")
    model.Params.OutputFlag = 0  # suppress solver output
    model.Params.TimeLimit = 10  # in seconds

    # Decision Variables
    z = model.addVars(C, vtype=GRB.BINARY, name="z")                   # 1 if card c is held
    y = model.addVars(C, M, vtype=GRB.BINARY, name="y")                # 1 if card c is activated in month m
    x = model.addVars(C, K, M, vtype=GRB.BINARY, name="x")             # 1 if category k routed to card c in month m
    R_ckm = model.addVars(C, K, M, lb=0.0, name="R_ckm")               # reward earned on category k from card c in month m
    R_cm = model.addVars(C, M, lb=0.0, name="R_cm")                    # total reward from card c in month m

    # Objective Function: total rewards over horizon minus one year of fees
    model.setObjective(
        gp.quicksum(R_cm[c, m] for c in C for m in M)
        - gp.quicksum(z[c] * eligible[c].annual_fee for c in C),
        GRB.MAXIMIZE,
    )

    # Constraints
    for m in M:
        # (1) Each category assigned to exactly one card
        for k in K:
            model.addConstr(gp.quicksum(x[c, k, m] for c in C) == 1)

        for c in C:
            card = eligible[c]
            routed = gp.quicksum(monthly_spend[k] * x[c, k, m] for k in K)

            # (2) Min spend lower bound
            model.addConstr(routed >= card.min_spend * y[c, m])

            # (3) Min spend upper bound (big-M = total spend)
            model.addConstr(routed <= total_spend * y[c, m])

            # (7) Activation requires holding
            model.addConstr(y[c, m] <= z[c])

            for k in K:
                # (4a) Per-category uncapped reward bound
                model.addConstr(R_ckm[c, k, m] <= card.rates[k] * monthly_spend[k] * x[c, k, m])

                # (4b) Per-category cap
                model.addConstr(R_ckm[c, k, m] <= card.category_caps[k])

                # (6) Category assignable only if card is activated
                model.addConstr(x[c, k, m] <= y[c, m])

            # (4c) Aggregate per-category rewards
            model.addConstr(R_cm[c, m] == gp.quicksum(R_ckm[c, k, m] for k in K))

            # (5) Overall monthly cap
            model.addConstr(R_cm[c, m] <= card.overall_cap)

    # (8) Wallet size limit
    model.addConstr(gp.quicksum(z[c] for c in C) <= max_cards)

    # Solve
    model.Params.TimeLimit = 10
    model.optimize()

    # Read Output Variables
    wallet = [eligible[c].id for c in C if z[c].X > 0.5 and eligible[c].id != "no_card"]

    # Month 0 is representative (spend is constant across months)
    allocation: dict[str, str] = {}
    for k in K:
        for c in C:
            if x[c, k, 0].X > 0.5:
                allocation[k] = eligible[c].id
                break

    monthly_reward = round(sum(R_cm[c, 0].X for c in C), 2)
    annual_fee = round(sum(eligible[c].annual_fee for c in C if z[c].X > 0.5), 2)

    return OptimizationResult(
        wallet=wallet,
        allocation=allocation,
        monthly_reward=monthly_reward,
        annual_fee=annual_fee,
        net_annual_reward=round(monthly_reward * 12 - annual_fee, 2),
    )
