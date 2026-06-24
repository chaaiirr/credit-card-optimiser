import json
from pathlib import Path
from pydantic import BaseModel

# Six spending categories used throughout the model
CATEGORIES = ["dining", "groceries", "online", "transport", "utilities", "travel"]

# Path to card rules dataset
_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "cards.json"


class Card(BaseModel):
    id: str
    name: str
    annual_fee: float
    min_income: float
    min_spend: float          # monthly minimum to activate rewards
    overall_cap: float        # monthly reward cap across all categories (999999 = uncapped)
    affiliate_url: str
    rates: dict[str, float]         # S$ reward per S$ spent per category
    category_caps: dict[str, float] # monthly reward cap per category (999999 = uncapped)


def load_cards() -> list[Card]:
    with open(_DATA_PATH) as f:
        return [Card(**entry) for entry in json.load(f)]
