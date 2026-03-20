# Agent Skill: Web Standards Archeologist (Paper Trail)

This skill enables the agent to trace any clause, element, algorithm, or GitHub issue/PR in Web Standards (WHATWG, W3C, WICG) back to its historical origins.

## 1. Repository Mapping & Caching
Always use `~/.gemini/cache/specs` for local clones to maintain a cross-session cache.

- **WHATWG HTML**: `https://github.com/whatwg/html` -> `whatwg-html/source`
- **WHATWG DOM**: `https://github.com/whatwg/dom` -> `whatwg-dom/dom.bs`
- **WHATWG Fetch**: `https://github.com/whatwg/fetch` -> `whatwg-fetch/fetch.bs`
- **W3C CSS**: `https://github.com/w3c/csswg-drafts` -> search `**/*.bs`
- **WICG**: `https://github.com/WICG/<repo>` -> search `*.bs` or `index.html`

**Action**: If the repo is missing from the cache, try to use github directly. Otherwise, clone it with `--depth 1000` (to preserve enough history for `git log -L`).

## 2. Locating the Source Line (Heuristics)
Given a fragment ID (e.g., `#the-script-element`), find the exact line in the source file:
1.  **Exact ID**: `grep -n 'id="fragment"' <file>`
2.  **Header Pattern**: `grep -niE "<h[1-6][^>]*>.*word1.*word2.*</h[1-6]>" <file>` (where words are from the fragment).
3.  **Definition Pattern**: `grep -niE "<dfn[^>]*>.*word1.*word2.*</dfn>" <file>`
4.  **CSS Property**: Search for `Name: <property-name>` inside a `propdef` block.

## 3. History Tracing (Deep Blame)
To find why a line changed, use:
```bash
git -C <repo_path> log -L <line>,<line>:<rel_file_path> --no-patch --pretty=format:"%H%n%an%n%ad%n%s%n%b%n---END---"
```
*Note: If the line was recently added, `git blame` might be faster to find the single "landing" commit.*

## 4. Extracting the "Paper Trail"
Analyze commit messages for the following patterns:
- **GitHub**: `GH#(\d+)` or `github.com/.../issues/(\d+)`
- **Bugzilla**: `w3.org/Bugs/Public/show_bug.cgi?id=(\d+)` or `Bug (\d+)`
- **Mailing Lists**: `lists.w3.org/Archives/Public/` (Search these archives for specific revisions).
- **SVN Revisions**: Extract `git-svn-id: .*@(\d+)`. Use this to search W3C mailing list archives:
  - `https://www.google.com/search?q=site:lists.w3.org+r<rev>`

## 5. Rationale Reconstruction
1.  Identify the **original commit** that introduced the logic.
2.  Follow the **GitHub PR** linked in that commit to find implementer discussions, e.g. in its "Closed" **Github Commit**.
3.  For older commits, find the **W3C Bugzilla** or **Mailing List** thread.
4.  Summarize the "Why": What browser bug was being fixed? What interoperability issue was addressed?
