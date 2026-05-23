# Work Plan: Python Conversion of Bluesky Scryfall Bot

## Overview

This is a line-for-line port of the TypeScript bot at `../scryfallbot` into Python.
The runtime target, AWS infrastructure, and feature set are identical — only the
language and toolchain change.  The CDK stack stays TypeScript (it is infrastructure
code, not bot code) but its user-data script must be updated to install Python
instead of Node.js.

## Technology Mapping

| TypeScript | Python equivalent |
|---|---|
| `@atproto/api` | `atproto` (https://atproto.blue) |
| `node-fetch` / built-in `fetch` | `httpx` |
| Jest | `pytest` |
| ESLint + Prettier | `ruff` (lint + format) |
| `ts-node --transpile-only` | `python main.py` (no compilation step) |
| TypeScript interfaces | Python `dataclasses` / `TypedDict` |
| `npm` / `package.json` | `pip` / `pyproject.toml` |

## Target Directory Layout

```
scryfallbot_python/
├── pyproject.toml          # project metadata, deps, pytest + ruff config
├── src/
│   └── bot/
│       ├── __init__.py
│       ├── query_parser.py     ← query-parser.ts
│       ├── card_lookup.py      ← card-lookup.ts
│       ├── card_formatter.py   ← card-formatter.ts
│       ├── bluesky_client.py   ← bluesky-client.ts
│       ├── metrics.py          ← metrics.ts
│       ├── bot.py              ← bot.ts
│       └── main.py             ← main.ts
└── tests/
    ├── __init__.py
    ├── test_query_parser.py
    ├── test_card_lookup.py
    ├── test_card_formatter.py
    ├── test_bluesky_client.py
    └── test_bot.py
```

---

## Phase 1: Project Initialisation ✓

### Step 1.1 — Create `pyproject.toml` ✓
- Python `>=3.11` (f-strings, `tomllib`, `match` statement available; AL2023 ships 3.11)
- Runtime dependencies: `atproto`, `httpx`
- Dev dependencies: `pytest`, `pytest-cov`, `ruff`
- Configure `[tool.pytest.ini_options]`: `testpaths = ["tests"]`
- Configure `[tool.ruff]`: target Python 3.11, enable pyflakes + pycodestyle rules

### Step 1.2 — Create directory skeleton ✓
- `src/bot/__init__.py` (empty)
- `tests/__init__.py` (empty)
- All source and test files as empty stubs so imports resolve before implementation

---

## Phase 2: Module Translations ✓

Each step below maps to one TypeScript source file.  Write the implementation
first, then its tests, then run `pytest` to confirm green before moving on.

### Step 2.1 — `query_parser.py`  ← `query-parser.ts` ✓

**What it does:** Parses `[[...]]` bracket syntax from a mention's text and returns
a list of card query objects.

**Python notes:**
- Use `re.finditer(r'\[\[([^\]]+)\]\]', text)` — identical regex to the TS version.
- Represent `CardQuery` as a `dataclass` with fields: `name: str`,
  `set: str | None`, `collector_number: str | None`,
  `mode: Literal['normal','image','prices','rulings','legality'] | None`.
- Mode prefix detection (`!`, `$`, `?`, `#`) is a straight `str.startswith` chain.

**Test coverage (mirrors `query-parser.test.ts`):**
- No brackets → empty list
- Single card: `[[Lightning Bolt]]`
- Set modifier: `[[Jace|WWK]]`
- Set + collector number: `[[Island|ZEN|235]]`
- All four mode prefixes
- Multiple queries in one string
- Empty name after prefix stripped → excluded
- Fuzzy / misspelled name passed through unchanged

---

### Step 2.2 — `metrics.py`  ← `metrics.ts` ✓

**What it does:** Writes a CloudWatch Embedded Metric Format (EMF) JSON line to
stdout.  The CloudWatch agent ships `/var/log/scryfallbot.log` to CloudWatch Logs,
which auto-extracts the metrics.

**Python notes:**
- `import json, time` — no external dependencies.
- `record_metric(name: str, dimensions: dict[str, str] | None = None) -> None`
- `int(time.time() * 1000)` for millisecond timestamp (equivalent to `Date.now()`).
- Write with `print(json.dumps(entry))` — `print` appends a newline, matching
  `console.log` behaviour.
- Wrap in `try/except Exception` so metric failures never affect the bot's core flow.

**Tests:** Unit-test the JSON structure written to stdout using `capsys` fixture.

---

### Step 2.3 — `card_lookup.py`  ← `card-lookup.ts` ✓

**What it does:** Wraps the Scryfall REST API.  Enforces a 1 req/sec rate limit,
backs off 30 s on 429, emits metrics for errors and rate-limit hits.

**Python notes:**
- Use `httpx.Client` (synchronous) — no async needed; the bot's poll loop is
  single-threaded already.
- Represent `CardData`, `CardPrices`, `ImageUris`, `CardFace`, `Ruling` as
  `dataclass` or `TypedDict`.  `TypedDict` is easier when deserialising raw API
  JSON because it avoids a separate construction step.
- `CardLookup.__init__` accepts an optional `client: httpx.Client` parameter for
  test injection (equivalent to the TS `FetchFn` approach).
- `_throttled_fetch(url)` tracks `self._last_request_at` using `time.monotonic()`.
- `time.sleep` is injected via a `sleep_fn` parameter (default `time.sleep`) for
  the same reason the TS version injects `SleepFn`.
- HTTP error handling: 404/422 → return `None`; other non-2xx → call
  `record_metric('ScryfallApiError')` then raise.

**Public methods:**
- `find_card(name, set_code=None, collector_number=None) -> CardData | None`
- `find_rulings(card: CardData) -> list[Ruling]`
- `fetch_image(card: CardData) -> bytes | None`

**Tests:** Inject a mock `httpx.Client` via `unittest.mock.MagicMock` (or
`httpx`'s own `MockTransport`).  Mirror the existing TS test cases for rate
limiting, 404, 422, 5xx, and double-faced card image URI fallback.

---

### Step 2.4 — `card_formatter.py`  ← `card-formatter.ts` ✓

**What it does:** Converts `CardData` into human-readable strings for Bluesky posts.

**Python notes:**
- `format_card`, `format_prices`, `format_legalities`, `format_rulings`,
  `card_not_found_message`, `scryfall_error_message` are all pure functions —
  direct line-for-line translation.
- `split_into_chunks(text, limit)`: Python's `str` iteration (`for ch in text`)
  already yields Unicode code points, not UTF-16 surrogate pairs, so the grapheme
  cluster concern from the TS version mostly disappears.  The loop logic is the
  same otherwise.
- `MAJOR_FORMATS` and `LEGALITY_LABELS` become module-level constants (plain lists
  and dicts).

**Tests:** Mirror `card-formatter.test.ts` — formatCard with/without mana cost,
prices with missing fields, legalities table, rulings with/without entries,
split_into_chunks word-boundary behaviour.

---

### Step 2.5 — `bluesky_client.py`  ← `bluesky-client.ts` ✓

**What it does:** Wraps the `atproto` Python SDK.  Fetches new mentions, uploads
images, and posts replies.

**Python notes:**
- `atproto.Client` is synchronous by default — use it directly.
- `StateStore` becomes a simple abstract base class (or Protocol) with `load() ->
  str | None` and `save(last_seen_at: str) -> None`.
- `Mention` and `BlobRef` become dataclasses.
- `get_new_mentions()` calls
  `client.app.bsky.notification.list_notifications(params={'limit': 50})`.
  Notification records from the `atproto` SDK are typed objects, not raw dicts —
  access fields via attributes (`.uri`, `.cid`, `.reason`, `.record`,
  `.indexed_at`).
- `upload_image(data: bytes, mime_type: str) -> BlobRef` calls
  `client.upload_blob(data, mime_type=mime_type)`.
- `reply_to_mention` and `reply_in_thread` call `client.send_post()` with the
  appropriate `reply` and `embed` parameters using `atproto` model objects
  (`models.AppBskyEmbedImages.*`).

**Tests:** Mock `atproto.Client` with `unittest.mock.MagicMock`.  Cover: cold-start
cursor defaulting to now, cursor advance and persistence, mention filtering by
`reason` and timestamp, image attach, threaded reply.

---

### Step 2.6 — `bot.py`  ← `bot.ts` ✓

**What it does:** The main polling loop.  Fetches mentions, routes each `CardQuery`
to the appropriate handler, posts replies, emits metrics.

**Python notes:**
- `Bot.__init__` accepts `bluesky: BlueskyClient`, `card_lookup: CardLookup`,
  `poll_interval_s: float = 5.0`, and `sleep_fn` for testability.
- `process_mentions()` is the direct equivalent of `processMentions()`.
- `start()` loops forever with `while True`.
- Mode dispatch (`normal`, `image`, `prices`, `rulings`, `legality`) is a
  `match query.mode:` statement — cleaner than the TS if/elif chain.
- Constants: `MAX_POST_GRAPHEMES = 300`, `MAX_CARDS_PER_MENTION = 4`.

**Tests:** Mirror `bot.test.ts`.  Patch `record_metric` via
`unittest.mock.patch('src.bot.metrics.record_metric')` to prevent EMF output
during tests.  Cover all five query modes, card-not-found, processing errors,
per-mention card limit enforcement.

---

### Step 2.7 — `main.py`  ← `main.ts` ✓

**What it does:** Entry point.  Reads env vars, constructs all objects, calls
`bot.start()`.

**Python notes:**
- `os.environ` for `BLUESKY_HANDLE` and `BLUESKY_APP_PASSWORD`.
- `StateStore` backed by `state.json` in the project root (same path logic as TS,
  using `pathlib.Path(__file__).parent.parent.parent / 'state.json'`).
- No dynamic import needed — `atproto` is a regular synchronous package.

---

## Phase 3: CDK Infrastructure Update ✓

The CDK stack is TypeScript, kept in a **separate private repo** at
`scryfallbot-infra/` (not in this public Python repo).

### Step 3.1 — Create `scryfallbot-infra` CDK project ✓
New project at `C:\Users\marcu\OneDrive\Documents\code\scryfallbot-infra` with:
- `lib/scryfallbot-infra-stack.ts` — full stack (EC2, IAM, CloudWatch, SNS)
- Python-specific user-data: installs `python3.11`, clones this repo,
  runs `pip install -r requirements.txt`, launches via `python3.11 -m bot.main`
- `PYTHONPATH=/opt/scryfallbot/src` set in start.sh (required for relative imports)
- Repo: `tayasteere/blueskyscryfallbot`

### Step 3.2 — Add `requirements.txt` ✓
Pinned runtime deps (`atproto==0.0.65`, `httpx==0.28.1`) read by the
user-data `pip install` command during instance bootstrap.

---

## Phase 4: Verification

- [x] `pytest --cov=src --cov-report=term-missing` — all tests green, coverage ≥ 90%
- [x] `ruff check src tests` — no lint errors
- [x] `ruff format --check src tests` — no formatting violations
- [x] Manual smoke test: run `python src/bot/main.py` locally with real credentials,
      send a `[[Lightning Bolt]]` mention, verify reply appears on Bluesky
- [ ] Deploy updated CDK stack and verify CloudWatch logs + metrics are populated

---

## Key Differences from the TypeScript Version

| Area | TypeScript | Python |
|---|---|---|
| Compilation | `tsc` / `ts-node --transpile-only` | None — run directly |
| Memory (swap) | 1 GB swap needed for `ts-node` | Not needed; Python's footprint is much smaller |
| Types | Compile-time enforced | Runtime hints only (use `mypy` for static checking if desired) |
| Async | `async/await` throughout | Synchronous; `time.sleep` for the poll interval |
| Import of Bluesky SDK | Dynamic `await import(...)` to handle ESM | Normal `import atproto` |
| Grapheme counting | `[...text]` spreads into Unicode clusters | `for ch in text` iterates code points; sufficient for Bluesky's limit |
