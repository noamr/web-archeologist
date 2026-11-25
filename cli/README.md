# web-archeologist CLI and codemode SDK

The `web-archeologist` skill is a protocol: it tells an agent where to look
and how to grep. For agents that call shell commands, carrying the whole
skill in context is expensive. This directory ships the mechanical parts
of the protocol as a tiny CLI, so one subcommand replaces a paragraph of
instructions.

## Install

```bash
npm install -g web-archeologist   # or `npm link` from a clone
web-archeologist --help
```

Requires Node >= 20. The CLI clones spec repos into
`~/.cache/web-archeologist/specs/` (override with
`WEB_ARCHEOLOGIST_CACHE`).

## Subcommands

Every subcommand prints a single JSON document on stdout; errors go there
too as `{"error": "..."}` with a nonzero exit code.

| Command | What it does |
| :--- | :--- |
| `xref <term>` | Look up a term through `respec.org/xref`. |
| `mdn <query> [--limit N]` | Top MDN docs for a query. |
| `resolve <spec-url>` | Clone the spec's repo and find the file + line where `<dfn>` for the URL's `#fragment` lives. |
| `blame <spec-url>` | `resolve`, then the earliest and latest commits that touched that line (uses `git log -S` pickaxe and `git blame`). |
| `irc <term> [--limit N]` | `grep` the WHATWG IRC logs clone (`KrijnHoetmer/irc-logs`). |
| `repo <spec-url>` | Just print the `(repo, file, fragment)` mapping without cloning. |

Example:

```bash
$ web-archeologist xref "fetch timing info" | jq
{
  "term": "fetch timing info",
  "hits": [
    { "spec": "fetch", "type": "dfn", "uri": "#fetch-timing-info", "normative": true }
  ]
}

$ web-archeologist blame "https://fetch.spec.whatwg.org/#main-fetch" | \
    jq '{file,line,first:.first.subject,last:.last.subject}'
{
  "file": "fetch.bs",
  "line": 4909,
  "first": "Overhaul how standards integrate with fetch",
  "last": "Overhaul how standards integrate with fetch"
}
```

## Codemode SDK shim

Agents that run in a `codemode`-style sandbox (QuickJS, no fs, no network,
only `tools.bash`) can wrap the CLI in a one-file SDK, so a script calls
`arch.resolve(url)` instead of shelling out and parsing JSON by hand. See
[`codemode/web-archeologist.js`](../codemode/web-archeologist.js):

```js
// Paste `makeArcheologist` from codemode/web-archeologist.js into your script.
const arch = makeArcheologist();
const dfn = await arch.resolve("https://fetch.spec.whatwg.org/#main-fetch");
const history = await arch.blame("https://fetch.spec.whatwg.org/#main-fetch");
```
