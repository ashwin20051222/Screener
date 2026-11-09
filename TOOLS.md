# TOOLS.md — Available Tools Inventory

> Phase 0 deliverable. Lists every REA and Antigravity tool available for this project, how each will be used, and any constraints.

## REA MCP Server Tools

### Browser / Web Inspection (our build verification)

| Tool | Purpose | How we use it |
|------|---------|---------------|
| `list_browser_targets` | List page targets on a loopback CDP endpoint | Find our running app's target ID for inspection |
| `inspect_web_page` | Passive DOM, accessibility, scripts, network, console inspection via CDP | Verify our app's DOM structure, check for console errors, validate accessibility |
| `capture_web_screenshot` | Capture viewport PNG of a running page | Take screenshots of our app for visual QA comparison |
| `compare_web_screenshots` | Pixel-level comparison of two PNG screenshots | Compare our app's rendering against reference screenshots |
| `compare_web_captures` | Compare full passive web captures (DOM + network + storage) | Deep before/after comparison of our app states |
| `observe_web_session` | Arm CDP observation window while user operates page | Watch our app during interactive testing |
| `capture_browser_scenario` | Run controlled browser scenario (goto, click, fill, wait) | Automated E2E testing of our app's UI states |
| `inspect_web_event_listeners` | List event listeners on a page | Verify our app's event handling |
| `inspect_web_network_capture` | Inspect network activity of a page | Verify our app's data fetching |

### Artifact / File Inspection (data file discovery)

| Tool | Purpose | How we use it |
|------|---------|---------------|
| `inspect_artifact` | Inspect archives and packages | Examine downloaded official data files (ZIP, XLS) |
| `extract_artifact` | Extract contents from archives | Unpack official data downloads for parser development |
| `compare_artifacts` | Compare artifact inventories | Detect changes in official data file formats between downloads |

### Binary / Code Analysis (NOT USED — forbidden per policy)

The following tools exist but are **not used** in this project per section 4 of the build prompt:
- All `procedure_*`, `decompile_*`, `binary_*`, `open_binary`, `close_binary` tools
- All `inspect_native_*`, `annotate_native_*`, `resolve_native_*` tools
- All `inspect_android_*`, `search_android_*`, `inspect_adb_*` tools
- All `inspect_macho`, `inspect_pe_*`, `inspect_evm_*` tools
- All `recover_javascript_sources`, `export_web_scripts` tools
- All `*jeb*` tools

### Other REA Tools (available but not primary)

| Tool | Purpose | Potential use |
|------|---------|---------------|
| `analyze_web_bundle` | Analyze web bundles | Could inspect our own build output |
| `compare_web_screenshots` | Pixel comparison | Primary visual QA tool |
| `discover_webmcp_tools` | Find WebMCP tools on a page | Not needed for our app |

## Antigravity Platform Tools

| Tool | Purpose | How we use it |
|------|---------|---------------|
| `read_file` | Read files | Read screenshots, source code, data files |
| `write_file` | Create files | Create project files, documents, code |
| `edit_file` | Edit existing files | Modify code, update docs |
| `run_command` | Execute shell commands | Build, test, git operations, start servers |
| `search_web` | Web search | Discover official data source URLs and documentation |
| `invoke_subagent` | Launch parallel work | Parallel analysis, research tasks |

## Key Constraints

1. **REA browser tools require a CDP endpoint** — must start app with `--remote-debugging-port` or similar
2. **`capture_browser_scenario` can launch its own browser** — needs `executable_path` for Chromium
3. **`compare_web_screenshots` needs base64 PNG data** — both images must be provided inline
4. **Official data discovery** will use `search_web` + manual verification, not REA browser tools against third-party sites (per REA policy section 4)
5. **No Tickertape inspection** — REA must never be pointed at Tickertape endpoints or assets

