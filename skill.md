# Agent Skill: Web Standards Archeologist (Paper Trail)

This skill enables the agent to trace any clause, element, algorithm, or GitHub issue/PR in Web Standards (WHATWG, W3C, WICG, IETF) back to its historical origins.

## 1. Cross-Spec Discovery (The "Map")
Before cloning repositories, use these tools to find the canonical definition and its impact across the web platform.

### A. Finding the Canonical Definition (ReSpec Xref)
If you only have a term (e.g., "fetch timing info") but no URL, use the ReSpec Xref service:
```bash
# Search for a term across all known specifications
curl -s "https://respec.org/xref/?term=fetch+timing+info" | grep -o 'https://[^"]*#[^"]*' | head -n 1
```

### B. Finding All References (WebDex)
To see which other specs depend on a definition, use WebDex (by @dontcallmedom). This helps identify the "Why" by seeing who *consumes* the logic:
- **Tool**: `http://dontcallmedom.github.io/webdex/`
- **Manual Search**: Search the term in WebDex to find "References" and "Definitions".

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

**Action**: Clone with `--depth 1000`. Use `git fetch --unshallow` if history is cut off.

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

## 4. History Tracing Strategies

### Strategy 1: Fast Pickaxe (Speed)
1. `git blame -L <line>,<line> <file>` to find the most recent landing SHA.
2. `git log -S "<exact_line_content>" --oneline --reverse <file>` to find the earliest commit.

### Strategy 2: Deep Line-Trace
For complex refactors where the prose was re-indented or moved:
- `git log -L <line>,<line>:<rel_file_path> --no-patch --pretty=format:"%H%n%an%n%ad%n%s%n%b%n---END---"`

## 5. Rationale Reconstruction
Analyze commit messages for:
- **Editor Intent**: `[e]` (Editorial), `[ct]` (Tree Construction), `[giow]` (Implementer).
- **Consensus**: `Resolution:` or `RESOLVED:` (Links to meeting minutes).
- **WPT Search**: `https://github.com/web-platform-tests/wpt/search?q=ID`
- **SVN**: `git-svn-id: .*@(\d+)` -> Search `https://www.google.com/search?q=site:lists.w3.org+rID`
