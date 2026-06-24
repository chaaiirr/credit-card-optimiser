from app.solver.optimizer import solve, OptimizationResult
from app.solver.cards import CATEGORIES

HIGH_SPEND = {
    "dining": 600, "groceries": 400, "online": 500,
    "transport": 200, "utilities": 150, "travel": 0,
}
LOW_SPEND = {cat: 50 for cat in CATEGORIES}


def test_returns_optimization_result():
    result = solve(HIGH_SPEND, income=60000, max_cards=3)
    assert isinstance(result, OptimizationResult)


def test_wallet_within_max_cards():
    result = solve(HIGH_SPEND, income=60000, max_cards=2)
    assert len(result.wallet) <= 2


def test_all_categories_allocated():
    result = solve(HIGH_SPEND, income=60000, max_cards=3)
    assert set(result.allocation.keys()) == set(CATEGORIES)


def test_allocated_cards_in_wallet():
    result = solve(HIGH_SPEND, income=60000, max_cards=3)
    for card_id in result.allocation.values():
        assert card_id in result.wallet


def test_net_reward_equals_rewards_minus_fees():
    result = solve(HIGH_SPEND, income=60000, max_cards=3)
    expected = round(result.monthly_reward * 12 - result.annual_fee, 2)
    assert abs(result.net_annual_reward - expected) < 0.01


def test_low_spend_still_feasible():
    result = solve(LOW_SPEND, income=30000, max_cards=3)
    assert isinstance(result, OptimizationResult)
    assert set(result.allocation.keys()) == set(CATEGORIES)
