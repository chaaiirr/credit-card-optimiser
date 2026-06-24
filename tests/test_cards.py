from app.solver.cards import load_cards, CATEGORIES


def test_six_categories():
    assert CATEGORIES == ["dining", "groceries", "online", "transport", "utilities", "travel"]


def test_loads_eleven_cards():
    assert len(load_cards()) == 11


def test_all_cards_have_all_categories():
    cards = load_cards()
    for card in cards:
        assert set(card.rates.keys()) == set(CATEGORIES)
        assert set(card.category_caps.keys()) == set(CATEGORIES)


def test_rates_in_valid_range():
    for card in load_cards():
        for rate in card.rates.values():
            assert 0.0 <= rate <= 0.20, f"{card.name} rate {rate} out of range"


def test_caps_non_negative():
    for card in load_cards():
        assert card.overall_cap > 0
        for cap in card.category_caps.values():
            assert cap > 0
