# TOOLS.md — Available Tools Inventory & MCP Connections

> Updated for `replica-v1.1+` live data & symbol resolution upgrade. Lists every MCP server (REA and official NSE MCPs), Antigravity platform tool, verified schemas, and strict licensing boundaries.

---

## 1. Official NSE MCP Servers (Streamable HTTP)

Configured safely alongside existing MCP servers in `~/.gemini/config/mcp_config.json` (preserving `rea`, `konnect`, and `kicad-mcp-pro` untouched):

| Server ID | Endpoint URL | Transport | Protocol Verified |
|---|---|---|---|
| `nse-bhavcopy` | `https://mcp.nseindia.in/bhavcopy/cm/mcp` | `streamable-http` | `2025-03-26` (`nse-bhavcopy-redis-mcp v1.0.0`) |
| `cm-market` | `https://mcp.nseindia.in/cmmkt/mcp` | `streamable-http` | `2025-03-26` (`cm-market-mcp v1.0.0`) |

### 1.1 `nse-bhavcopy` — Discovered Tools (21 tools)

Official description: *Serves historical OHLCV data for ~5000 NSE-listed equities (5-year hot window, official NSE Bhavcopy files).*

- **Symbol Resolution & Lookup:**
  - `search_symbols(query)` *(required: `query`)*
  - `nse_lookup_symbol(query)` *(required: `query`)*
- **Stock History, Quotes & Technicals:**
  - `get_ltp_by_date(symbol, date)` *(required: `symbol`, `date` `yyyy-MM-dd`)*
  - `get_bulk_quote(symbols)` *(required: `symbols`, max 50 stocks)*
  - `get_stock_history(symbol, months, endDate)` *(required: `symbol`, `months`, `endDate`; up to 3 months per call)*
  - `get_52_week_high_low(symbol)` *(required: `symbol`)*
  - `moving_average(symbol, days)` *(required: `symbol`, `days`)*
  - `get_volume_analysis(symbol, days)` *(required: `symbol`, `days`)*
  - `get_corporate_actions(symbol, fromDate, toDate)` *(required: `symbol`, `fromDate`, `toDate`)*
  - `compare_stocks(symbols, months)` *(required: `symbols`, `months`)*
  - `get_stock_vs_index(symbol, indexName, months, date)`
- **Market & Index Tools:**
  - `get_top_by_volume(date, n, sortBy)` (`sortBy`: `'volume' | 'value'`)
  - `get_top_movers(date, n, direction)` (`direction`: `'gain' | 'loss'`)
  - `get_market_mood(date)`, `get_market_breadth(date)`
  - `get_index_snapshot(date, filter)`, `get_index_performance(indexName, date)`, `get_index_history(indexName, months, endDate)`, `get_index_valuation(indexName, months, date)`, `compare_indices(indexNames, months, date)`, `get_index_movers(date, period, n, scope)`

### 1.2 `cm-market` — Discovered Tools (15 tools)

Official description: *Serves live NSE cash-market data (~1 minute refresh for stocks/indices, 5-minute refresh for gainers/losers).*

- **Symbol & Equity Quotes (1-min delayed):**
  - `cm_get_equity_stocks(limit, symbolFilter)` *(series EQ/BE/BL/BT/IL/IQ; `limit` up to 500)*
  - `cm_get_stock_quote(symbol)` *(required: `symbol`)*
  - `cm_get_call_auction_stocks(limit, symbolFilter)`
  - `cm_get_bond_stocks(limit, symbolFilter)`
  - `cm_get_sme_stocks(limit, symbolFilter)`
- **Indices, Movers & Market Status:**
  - `cm_get_index_quote(indexName)`, `cm_get_live_indices(group, nameFilter)`
  - `cm_get_live_market_data(index)` (`'gainers' | 'loosers'`)
  - `cm_get_live_gainers()`, `cm_get_live_losers()`
  - `nse_get_gainers(limit)`, `nse_get_losers(limit)`, `nse_get_market_movers(indexName, limit)`
  - `cm_get_data_status()`, `cm_get_allstocks_status()`

### 1.3 Live Verification Results (`2026-11-10`)

- `nse-bhavcopy.search_symbols({"query": "Reliance"})` → HTTP 200 MCP SSE JSON-RPC: `{"results":[{"symbol":"RELIANCE","last_close":1324.4,"pct_change":0.03,"last_date":"2026-11-09"}],"count":1}`
- `nse-bhavcopy.get_ltp_by_date({"symbol": "INFY", "date": "2026-11-06"})` → HTTP 200 MCP SSE JSON-RPC: `1181.4`
- `cm-market.tools/list` → HTTP 200 listing 15 cash-market delayed tools.
- Note on schema mismatch across servers: `nse-bhavcopy` defines `nse_lookup_symbol(query)` while `cm-market` does not expose `nse_lookup_symbol` cleanly in `tools/list` (uses `cm_get_stock_quote(symbol)` / `cm_get_equity_stocks(limit, symbolFilter)`). Always inspect each server's `tools/list` schema before invocation.

### 1.4 Strict Usage & Licensing Boundary

Per official NSE MCP terms (`https://www.nseindia.in/nse-mcp`):
- **Permitted here:** Agent-side research, symbol verification, QA cross-checks of official prices/corporate actions, and development diagnostics.
- **Strictly Prohibited:** Treating NSE MCP as a licensed production market-data feed for ScreenerDesk, bulk-extracting/dumping MCP responses into `data/screener.db`, or routing redistributable/commercial product feeds through MCP endpoints. Production data continues exclusively through official UDiFF/archive downloads (`ingest/`), AMFI/XBRL filings, or a user-configured authorized live vendor (`app/providers/`).

---

## 2. REA MCP Server Tools (Existing)

### Browser / Web Inspection (build & UI QA)

| Tool | Purpose | How we use it |
|---|---|---|
| `list_browser_targets` | List page targets on a loopback CDP endpoint | Find our running app's target ID for inspection |
| `inspect_web_page` | Passive DOM, accessibility, scripts, network, console inspection via CDP | Verify DOM, accessibility, zero console errors |
| `capture_web_screenshot` | Capture viewport PNG of a running page | Visual QA verification |
| `compare_web_screenshots` | Pixel-level comparison of two PNG screenshots | Compare rendering against reference screenshots |
| `compare_web_captures` | Compare full passive web captures (DOM + network + storage) | Before/after app state comparison |
| `observe_web_session` | Arm CDP observation window | Interactive session inspection |
| `capture_browser_scenario` | Controlled Chromium launch + Playwright scenario + network/console event capture | End-to-end QA of add-filter ensure flow & auto-refresh |
| `inspect_web_event_listeners` | Inspect DOM event listeners | Event binding verification |
| `inspect_web_network_capture` | Inspect network XHR/fetch activity | Verify `/api/data/ensure`, `/api/coverage`, `/api/screener/dataset` |

### Binary / Code Analysis (NOT USED — forbidden per policy)
All `procedure_*`, `decompile_*`, `binary_*`, `open_binary`, `inspect_native_*`, `inspect_android_*`, `*jeb*`, `recover_javascript_sources` tools remain unused. Never point REA at Tickertape assets/APIs.

---

## 3. Antigravity Platform Tools & Constraints

- Core tools: `read_file`, `write_file`, `edit_file`, `run_command`, `search_web`, `invoke_subagent`.
- Chromium executable for REA `capture_browser_scenario`: `/home/silicondoc/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome`.
- Antigravity configuration location: `~/.gemini/config/mcp_config.json` (Streamable HTTP transport via `"url"` supported natively per `agy-customizations/docs/mcp_servers.md`; note newly added MCP servers take effect on next Antigravity MCP reload, and were verified directly via Streamable HTTP JSON-RPC `initialize` / `tools/list` / `tools/call`).
