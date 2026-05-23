# Bluesky Scryfall Bot

A Bluesky bot that looks up Magic: The Gathering cards via the [Scryfall API](https://scryfall.com/docs/api) and replies with card details, prices, rulings, legality, or card images.

## Usage

Mention the bot in any Bluesky post with card names wrapped in double brackets:

```
@scryfallbot.bsky.social [[Lightning Bolt]]
```

### Query syntax

| Prefix | Mode | Example |
|--------|------|---------|
| *(none)* | Card text + image | `[[Lightning Bolt]]` |
| `!` | Image only | `[[!Lightning Bolt]]` |
| `$` | Prices (USD, EUR, MTGO TIX) | `[[$Lightning Bolt]]` |
| `?` | Official rulings | `[[?Lightning Bolt]]` |
| `#` | Format legalities | `[[#Lightning Bolt]]` |
| `*` | Random card (text + image) | `[[*]]` |

You can pin a specific printing using set code and collector number:

```
[[Lightning Bolt|lea]]          ← by set code
[[Lightning Bolt|lea|62]]       ← by set code + collector number
```

Up to **4 cards** can be looked up per mention. Additional cards require a separate mention.

## Setup

### Prerequisites

- Python 3.11+
- A Bluesky account and an [app password](https://bsky.app/settings/app-passwords)

### Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### Configure

Set the following environment variables:

```
BLUESKY_HANDLE=yourbot.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
SCRYFALL_USER_AGENT=YourBotName/1.0
```

`SCRYFALL_USER_AGENT` identifies your bot to Scryfall. Use a unique name — Scryfall tracks usage per user agent, so running multiple bots with the same string conflates their traffic.

### Run

```bash
python -m bot.main
```

The bot polls for new mentions every 5 seconds. On first run it skips all pre-existing notifications; on subsequent runs it resumes from `state.json` in the project root.

## Configuration

Bot behaviour can be tuned by placing a `config.toml` file in the project root. All keys are optional — omitting a key uses the default shown below.

```toml
[bot]
poll_interval_seconds = 5   # how often to check for new mentions
max_cards_per_mention = 4   # maximum cards looked up in a single mention

[rate_limiting]
window_seconds = 60              # length of the rate limit window
max_mentions_per_window = 5      # mentions allowed per user per window
violation_window_seconds = 600   # window over which violations are counted
violations_before_warning = 3    # violations before a warning reply is sent
violations_before_block = 5      # violations before the user is blocked
```

If no `config.toml` is present the defaults above are used.

## Abuse prevention

The bot tracks mentions per user and enforces a rate limit to prevent spam.

- **Rate limiting** — each user may send up to 5 mentions per 60-second window. Mentions beyond this are silently dropped.
- **Warnings** — after 3 rate limit violations within a 10-minute window, the user receives a single warning reply.
- **Blocking** — after 5 violations, the user is permanently blocked via the Bluesky API. Blocks persist across restarts; the bot fetches the existing block list from Bluesky on startup.

All thresholds are configurable via `config.toml`.

## Development

Install dev dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
pytest --cov=bot  # with coverage
```

Lint:

```bash
ruff check src tests
```

## Project structure

```
src/bot/
  main.py           — entry point, wires up dependencies
  bot.py            — poll loop and mention processing logic
  bluesky_client.py — atproto wrapper (auth, notifications, replies, blocks)
  card_lookup.py    — Scryfall API client with rate limiting
  card_formatter.py — formats card data into reply text
  query_parser.py   — parses [[card]] syntax from post text
  rate_limiter.py   — per-user rate limiting and block decisions
  config.py         — configuration dataclasses and config.toml loader
  metrics.py        — lightweight metric recording
```

## License

Copyright 2026 Taya Steere. Licensed under the [Apache License, Version 2.0](LICENSE).

## Scryfall API rate limiting

The bot enforces Scryfall's 1 request/second policy between API calls and backs off 30 seconds on HTTP 429 responses.
