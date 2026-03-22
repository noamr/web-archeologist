# Agent Skill: Web Standards Archeologist (Paper Trail)

This skill enables the agent to trace any clause, element, algorithm, or GitHub issue/PR in Web Standards (WHATWG, W3C, WICG, IETF) back to its historical origins.

## 1. Repository Mapping & Caching
Always use `~/.gemini/cache/specs` for local clones to maintain a persistent cache.

### Mapping Table:
| Domain | GitHub Repository |
| :--- | :--- |
| `html.spec.whatwg.org` | `whatwg/html` (File: `source`) |
| `dom.spec.whatwg.org` | `whatwg/dom` (File: `dom.bs`) |
| `fetch.spec.whatwg.org` | `whatwg/fetch` (File: `fetch.bs`) |
| `*.spec.whatwg.org` | `whatwg/<name>` (File: `<name>.bs`) |
| `drafts.csswg.org` | `w3c/csswg-drafts` (Search `**/*.bs`) |
| `drafts.fxtf.org` | `w3c/fxtf-drafts` |
| `svgwg.org` | `w3c/svgwg` |
| `httpwg.org` | `httpwg/http-extensions` |
| `datatracker.ietf.org` | `httpwg/http-extensions` (HTTP-related) |
| `wicg.github.io` | `WICG/<name>` |

**Action**: Clone with `--depth 1000`. Use `git fetch --unshallow` if history is cut off before the target rationale is found.

## 2. Locating "The Definition" (Heuristics)
Given a fragment ID (e.g., `#main-fetch`), find the exact line. **The true definition is the `<dfn>` or structural block defining the term.**

### Step 1: Find the File
- **WHATWG HTML**: Always `source`.
- **IETF**: Search for RFC number in filename or `grep -rl fragment`.
- **General**: `grep -rlE "<dfn[^>]*.*fragment" . --include=*.bs --include=source --include=*.md`

### Step 2: Find the Line
Search for the fragment name using these patterns in order:
1.  **Strict <dfn> Attribute Match**:
    -   Common prefixes: `(concept-|rel-|attr-|dom-)?`
    -   `grep -nE '<dfn[^>]* (id|data-x)=["'\'']prefix?fragment["'\'']' <file>`
2.  **Multi-line <dfn> Handling**:
    -   If the fragment is inside a nested tag (e.g., `rel-help` in `<code>`), use `grep -nE 'data-x="fragment"'` then scan back 5 lines with `sed` to find the opening `<dfn`.
3.  **CSS Property**: `grep -nE "Name:\s*fragment" <file>` (Inside a `propdef` block).
4.  **Structural Anchor**: `grep -niE "<h[1-6][^>]*id=["'\'']fragment["'\'']" <file>`

## 3. History Tracing Strategies

### Strategy 1: Fast Pickaxe (Recommended)
1. `git blame -L <line>,<line> <file>` to find the most recent landing SHA.
2. `git log -S "<exact_line_content>" --oneline --reverse <file>` to find the earliest commit where this prose appeared.

### Strategy 2: Deep Line-Trace
For complex refactors where the prose was re-indented or moved:
- `git log -L <line>,<line>:<rel_file_path> --no-patch --pretty=format:"%H%n%an%n%ad%n%s%n%b%n---END---"`

## 4. Extracting the "Paper Trail"
Analyze commit messages for these markers:
- **Editor Intent**: 
  - `[e]` = Editorial (Usually safe to skip)
  - `[ct]` = Tree Construction
  - `[giow]` = General/Implementer rationale
- **GitHub**: `GH#(\d+)` -> Search WPTs at `https://github.com/web-platform-tests/wpt/search?q=ID`
- **Consensus**: `Resolution:` or `RESOLVED:` (Indicates a WG meeting decision).
- **SVN Revisions**: `git-svn-id: .*@(\d+)` -> Search `https://www.google.com/search?q=site:lists.w3.org+rID`

## 5. Rationale Reconstruction
1. Identify the **Normative** commit that introduced the logic.
2. Follow the **GitHub PR** or **Mailing List** thread.
3. Cross-Correlate between standards (e.g., HTML change vs Fetch algorithm update).
4. Summarize the technical and implementer rationale.
