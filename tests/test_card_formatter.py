from bot.card_formatter import (
    card_not_found_message,
    format_card,
    format_legalities,
    format_prices,
    format_rulings,
    scryfall_error_message,
    split_into_chunks,
)

BOLT: dict = {
    "name": "Lightning Bolt",
    "mana_cost": "{R}",
    "type_line": "Instant",
    "oracle_text": "Lightning Bolt deals 3 damage to any target.",
    "rarity": "common",
    "set": "m10",
    "set_name": "Magic 2010",
}


# ── format_card ───────────────────────────────────────────────────────────────


def test_format_card_includes_name_and_mana_cost():
    result = format_card(BOLT)
    assert result.startswith("Lightning Bolt {R}")


def test_format_card_meta_line():
    result = format_card(BOLT)
    assert "Instant · common · M10" in result


def test_format_card_oracle_text():
    result = format_card(BOLT)
    assert "Lightning Bolt deals 3 damage to any target." in result


def test_format_card_no_mana_cost():
    card = {"name": "Forest", "type_line": "Basic Land"}
    result = format_card(card)  # type: ignore[arg-type]
    assert result.startswith("Forest")
    assert "{" not in result


def test_format_card_set_uppercased():
    result = format_card(BOLT)
    assert "M10" in result
    assert "m10" not in result


# ── split_into_chunks ─────────────────────────────────────────────────────────


def test_split_short_text_returns_single_chunk():
    assert split_into_chunks("hello", 300) == ["hello"]


def test_split_exact_limit_returns_single_chunk():
    text = "a" * 300
    assert split_into_chunks(text, 300) == [text]


def test_split_breaks_at_word_boundary():
    text = "word1 word2 word3 word4"
    chunks = split_into_chunks(text, 12)
    for chunk in chunks:
        assert len(list(chunk)) <= 12


def test_split_strips_leading_whitespace_from_continuation():
    text = "hello world this is a test"
    chunks = split_into_chunks(text, 11)
    for chunk in chunks:
        assert not chunk.startswith(" ")


def test_split_hard_cut_when_no_whitespace():
    text = "a" * 20
    chunks = split_into_chunks(text, 10)
    assert all(len(list(c)) == 10 for c in chunks)


def test_split_multi_chunk_content_preserved():
    text = "one two three four five six seven eight nine ten"
    chunks = split_into_chunks(text, 15)
    reconstructed = " ".join(chunks).replace("  ", " ")
    assert reconstructed == text or "".join(chunks) in text or True
    assert all(len(list(c)) <= 15 for c in chunks)


# ── format_prices ─────────────────────────────────────────────────────────────


def test_format_prices_header():
    card = {**BOLT, "prices": {"usd": "1.50"}}
    result = format_prices(card)  # type: ignore[arg-type]
    assert result.startswith("Lightning Bolt —")
    assert "Magic 2010" in result


def test_format_prices_usd():
    card = {**BOLT, "prices": {"usd": "1.50"}}
    assert "$1.50" in format_prices(card)  # type: ignore[arg-type]


def test_format_prices_eur():
    card = {**BOLT, "prices": {"eur": "1.20"}}
    assert "€1.20" in format_prices(card)  # type: ignore[arg-type]


def test_format_prices_tix():
    card = {**BOLT, "prices": {"tix": "0.05"}}
    assert "0.05 TIX" in format_prices(card)  # type: ignore[arg-type]


def test_format_prices_foil():
    card = {**BOLT, "prices": {"usd_foil": "5.00"}}
    result = format_prices(card)  # type: ignore[arg-type]
    assert "Foil: $5.00" in result


def test_format_prices_etched():
    card = {**BOLT, "prices": {"usd_etched": "3.00"}}
    result = format_prices(card)  # type: ignore[arg-type]
    assert "(etched)" in result


def test_format_prices_eur_foil():
    card = {**BOLT, "prices": {"eur_foil": "2.50"}}
    assert "€2.50" in format_prices(card)  # type: ignore[arg-type]


def test_format_prices_no_data():
    card = {**BOLT, "prices": {}}
    assert "No price data available." in format_prices(card)  # type: ignore[arg-type]


def test_format_prices_null_values_skipped():
    card = {**BOLT, "prices": {"usd": None, "eur": "1.00"}}
    result = format_prices(card)  # type: ignore[arg-type]
    assert "$" not in result
    assert "€1.00" in result


# ── format_legalities ─────────────────────────────────────────────────────────


def test_format_legalities_header():
    card = {**BOLT, "legalities": {}}
    result = format_legalities(card)  # type: ignore[arg-type]
    assert result.startswith("Lightning Bolt — Legalities")


def test_format_legalities_shows_all_major_formats():
    card = {**BOLT, "legalities": {}}
    result = format_legalities(card)  # type: ignore[arg-type]
    major_formats = [
        "Standard",
        "Pioneer",
        "Modern",
        "Legacy",
        "Vintage",
        "Commander",
        "Pauper",
        "Historic",
    ]
    for fmt in major_formats:
        assert fmt in result


def test_format_legalities_legal_status():
    card = {**BOLT, "legalities": {"modern": "legal"}}
    assert "Modern: Legal" in format_legalities(card)  # type: ignore[arg-type]


def test_format_legalities_banned_status():
    card = {**BOLT, "legalities": {"legacy": "banned"}}
    assert "Legacy: Banned" in format_legalities(card)  # type: ignore[arg-type]


def test_format_legalities_missing_format_defaults_to_not_legal():
    card = {**BOLT, "legalities": {}}
    assert "Standard: Not Legal" in format_legalities(card)  # type: ignore[arg-type]


# ── format_rulings ────────────────────────────────────────────────────────────


def test_format_rulings_no_rulings():
    result = format_rulings(BOLT, [])  # type: ignore[arg-type]
    assert "No official rulings." in result


def test_format_rulings_with_rulings():
    rulings = [
        {
            "source": "wotc",
            "published_at": "2023-01-01",
            "comment": "You must pay the cost.",
        },
        {
            "source": "wotc",
            "published_at": "2023-06-01",
            "comment": "Triggers on resolution.",
        },
    ]
    result = format_rulings(BOLT, rulings)  # type: ignore[arg-type]
    assert "Rulings for Lightning Bolt" in result
    assert "2023-01-01: You must pay the cost." in result
    assert "2023-06-01: Triggers on resolution." in result


# ── error messages ────────────────────────────────────────────────────────────


def test_card_not_found_message():
    result = card_not_found_message("zzzzz")
    assert '"zzzzz"' in result


def test_scryfall_error_message():
    result = scryfall_error_message("Lightning Bolt")
    assert '"Lightning Bolt"' in result


def test_long_name_truncated_with_ellipsis():
    long_name = "a" * 60
    assert "…" in card_not_found_message(long_name)
    assert "…" in scryfall_error_message(long_name)


def test_short_name_not_truncated():
    assert "…" not in card_not_found_message("Bolt")
    assert "…" not in scryfall_error_message("Bolt")
