# Agent Skill: Web Standards Archeologist (Paper Trail)

This skill enables the agent to trace any clause, element, algorithm, or GitHub issue/PR in Web Standards (WHATWG, W3C, WICG, IETF) back to its historical origins.

## 1. Cross-Spec Discovery (The "Map")
Before cloning repositories, use these tools to find the canonical definition and its impact across the web platform.

### A. Finding the Canonical Definition (ReSpec Xref)
If you only have a term (e.g., "fetch timing info") but no URL, use the ReSpec Xref API:
```bash
# Search for a term across all known specifications
curl -s -X POST "https://respec.org/xref" \
  -H "Content-Type: application/json" \
  -d '{"keys": [{"term": "fetch timing info"}]}' | jq '.result[][1][0].uri'
```

### B. Finding All References (WebDex)
To see which other specs depend on a definition, use WebDex (by @dontcallmedom). This helps identify the "Why" by seeing who *consumes* the logic:
- **Tool**: `http://dontcallmedom.github.io/webdex/`
- **Manual Search**: Search the term in WebDex to find "References" and "Definitions".

### C. Universal Search (WebSpec Index)
For a comprehensive search across all modern and historical web specifications:
- **CLI Repository**: [jnjaeschke/webspec-index](https://github.com/jnjaeschke/webspec-index)
- **Usage**: Install with `cargo binstall webspec-index`. This tool provides full-text search, cross-reference tracking, and graph traversal across HTML, DOM, URL, CSS, ECMAScript, and 70+ other specifications. Use this to find where terms are defined if ReSpec Xref fails or if you need to build a cross-reference graph.

## 2. Repository Mapping & Caching
Always use `~/.gemini/cache/specs` for local clones.

### Mapping Table:
| Domain | GitHub Repository |
| :--- | :--- |
| `html.spec.whatwg.org` | `whatwg/html` (File: `source`) |
| `dom.spec.whatwg.org` | `whatwg/dom` (File: `dom.bs`) |
| `fetch.spec.whatwg.org` | `whatwg/fetch` (File: `fetch.bs`) |
| `*.spec.whatwg.org` | `whatwg/<name>` (File: `<name>.bs`) |
| `drafts.csswg.org` | `w3c/csswg-drafts` (Search `**/*.bs`) |
| `httpwg.org` | `httpwg/http-extensions` |
| `wicg.github.io` | `WICG/<name>` |
| `source.chromium.org` | `chromium/chromium` |
| `webkit.org` | `WebKit/WebKit` |
| `searchfox.org` | `mozilla/gecko-dev` |

**Action**: Clone with `--depth 1000`. Use `git fetch --unshallow` if history is cut off.
> **Warning**: A shallow clone (`--depth`) can lead to hallucinations where the oldest commit in the shallow history is incorrectly identified as the origin of a line. Always `git fetch --unshallow` before performing a deep history trace or `git log -L`.

## 3. Locating "The Definition" (Heuristics)
Given a fragment ID (e.g., `#main-fetch`), find the exact line. **The true definition is the `<dfn>` or structural block defining the term.**

### Step 1: Find the File
`grep -rlE "<dfn[^>]*.*fragment" . --include=*.bs --include=source --include=*.md`

### Step 2: Find the Line
Search for the fragment name using these patterns in order:
1.  **Strict <dfn> Attribute Match**:
    -   Common prefixes: `(concept-|rel-|attr-|dom-)?`
    -   `grep -nE '<dfn[^>]* (id|data-x)=["'\'']prefix?fragment["'\'']' <file>`
2.  **Multi-line <dfn> Handling**:
    -   If the fragment is inside a nested tag, use `grep -nE 'data-x="fragment"'` then scan back 5 lines with `sed` to find the opening `<dfn`.
3.  **CSS Property**: `grep -nE "Name:\s*fragment" <file>` (Inside a `propdef` block).

### Step 3: Browser Engine Source Discovery
If given a link to `source.chromium.org`, WebKit's GitHub, or Mozilla Searchfox:
- **Chromium**: Remove the URL prefix (e.g., `source.chromium.org/chromium/chromium/src/+/main:`) to isolate the file path.
- **WebKit**: Remove the URL prefix (e.g., `github.com/WebKit/WebKit/blob/main/`) to isolate the file path.
- **Mozilla (Gecko)**: Remove the URL prefix (e.g., `searchfox.org/mozilla-central/source/`) to isolate the file path.
- **Function Search**: If searching for a symbol name (e.g., `FetchManager::Loader::Start`), use `grep -rn "SymbolName" .` to find the implementation.

## 4. History Tracing Strategies
... (Strategies omitted for brevity) ...

## 5. Tracing Informal Discussions (IRC/Matrix)
When GitHub issues or Bugzilla reports reference a "discussion on IRC" or when you need to find the real-time debate behind a 2006-2016 era change:

### A. WHATWG IRC Logs (Historical)
- **Archive**: [krijnhoetmer.nl/irc-logs/](https://krijnhoetmer.nl/irc-logs/)
- **Search Tip**: Use Google with `site:krijnhoetmer.nl/irc-logs/whatwg "term"` to find specific discussions. This is the primary archive for the formative years of WHATWG.

### B. Modern WHATWG Logs (Matrix)
- **Archive**: [matrixlogs.bakkot.com/irc-whatwg/](https://matrixlogs.bakkot.com/irc-whatwg/)
- **Usage**: Use this for more recent discussions (post-2018) that happened in the #whatwg channel, now bridged to Matrix.

## 8. Spec Annotated Call Graph Construction
Use this protocol to build a tree of callers and callees for a specific algorithm or concept, annotating the relationships with spec links and rationale.

### A. Finding Callees (Internal Dependencies)
1.  **Locate the Definition Block**: Use the heuristics in Section 3 to find the `<div algorithm>` or structural block.
2.  **Scan for References**: Identify all `<a>` tags or terms in `[= ... =]` or `{{ ... }}` brackets within the block.
3.  **Resolve Specs**: For each reference, determine if it is internal (same file) or external (use ReSpec Xref to find the source spec).
4.  **Describe Relationship**: Note how the callee is used (e.g., "Invoked to validate the origin", "Passed as an argument to initialize the fetch params").

### B. Finding Callers (Incoming Dependencies)
1.  **Internal Callers**: `grep` the current specification for the term's `id` or `lt` (link text).
2.  **External Callers**: Use **WebDex** (`http://dontcallmedom.github.io/webdex/`) to find which other specifications reference this definition.
3.  **Rationale**: Analyze the calling context to describe *why* this spec is invoking the algorithm.

### C. Output Format (The Tree)
Present the graph as a nested Markdown list with the following structure:
- `Algorithm Name` [Spec Link] - "Short description of the algorithm's purpose."
  - **Callees**:
    - `Child Algorithm` [Spec Link] - "Relationship: [How it's used]"
  - **Callers**:
    - `Parent Algorithm` [Spec Link] - "Relationship: [Why it calls this]"

**Example**:
- `Main Fetch` [fetch/#main-fetch] - "The entry point for all network requests."
  - **Callees**:
    - `HTTP-network-or-cache fetch` [fetch/#http-network-or-cache-fetch] - "Relationship: Invoked for HTTP(S) schemes."
  - **Callers**:
    - `HTML Navigation` [html/#navigate] - "Relationship: Used to fetch the document resource."

