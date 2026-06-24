from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

_VALID_FORM = {
    "dining": "500", "groceries": "300", "online": "400",
    "transport": "150", "utilities": "200", "travel": "0",
    "income": "60000", "max_cards": "3",
}


def test_index_returns_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_optimize_returns_html():
    r = client.post("/optimize", data=_VALID_FORM)
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_optimize_shows_monthly_reward():
    r = client.post("/optimize", data=_VALID_FORM)
    assert "Monthly Reward" in r.text


def test_optimize_negative_income_returns_422():
    bad = {**_VALID_FORM, "income": "-1"}
    r = client.post("/optimize", data=bad)
    assert r.status_code == 422
