from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.solver.optimizer import solve
from app.solver.cards import load_cards, CATEGORIES

app = FastAPI(title="SG Card Optimizer")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "categories": CATEGORIES,
    })


@app.post("/optimize", response_class=HTMLResponse)
def optimize(
    request: Request,
    dining: float = Form(..., ge=0),
    groceries: float = Form(..., ge=0),
    online: float = Form(..., ge=0),
    transport: float = Form(..., ge=0),
    utilities: float = Form(..., ge=0),
    travel: float = Form(..., ge=0),
    income: float = Form(..., gt=0),
    max_cards: int = Form(default=3, ge=1, le=5),
):
    monthly_spend = {
        "dining": dining, "groceries": groceries, "online": online,
        "transport": transport, "utilities": utilities, "travel": travel,
    }
    result = solve(monthly_spend, income=income, max_cards=max_cards)
    cards_by_id = {c.id: c for c in load_cards()}
    cards_by_id["no_card"] = None  # excluded from display

    return templates.TemplateResponse(request, "results.html", {
        "result": result,
        "cards_by_id": cards_by_id,
        "monthly_spend": monthly_spend,
        "categories": CATEGORIES,
    })


@app.get("/health")
def health():
    return {"status": "ok"}

