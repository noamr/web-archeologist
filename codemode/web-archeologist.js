// web-archeologist SDK shim for `codemode`-style sandboxes.
//
// The whole point: a model inside a codemode sandbox (QuickJS, no network, no
// fs, only a `tools.bash({ command })` escape hatch) should not have to carry
// the 150-line skill in context just to run one lookup. Paste this file into
// the script, or install it as a reusable snippet the agent can import, and
// then call:
//
//   const arch = makeArcheologist();
//   const hits = await arch.xref("fetch timing info");
//   const dfn = await arch.resolve("https://fetch.spec.whatwg.org/#main-fetch");
//
// Every method returns the parsed JSON the CLI printed, or throws with the
// `error` field on failure. Keep this file dependency-free: it must drop into
// a sandbox that has no `require`, no `import`, no fs, just `tools.bash`.

function makeArcheologist(options) {
  const bin = (options && options.bin) || "web-archeologist";
  const bash = (options && options.bash) || (typeof tools !== "undefined" ? tools.bash : null);
  if (!bash) {
    throw new Error("makeArcheologist: no bash() available; pass options.bash");
  }

  const shellQuote = (s) => `'${String(s).replace(/'/g, "'\\''")}'`;

  const call = async (subcmd, args) => {
    const parts = [bin, subcmd, ...args.map(shellQuote)];
    const result = await bash({ command: parts.join(" ") });
    const out = typeof result === "string" ? result : (result.output ?? "");
    const exit = typeof result === "object" ? result.exit_code : 0;
    let parsed;
    try { parsed = JSON.parse(out.trim().split("\n").pop()); }
    catch (_) { throw new Error(`web-archeologist ${subcmd}: non-JSON output: ${out.slice(0, 200)}`); }
    if (parsed && parsed.error) throw new Error(`web-archeologist ${subcmd}: ${parsed.error}`);
    if (exit && exit !== 0) throw new Error(`web-archeologist ${subcmd}: exit ${exit}`);
    return parsed;
  };

  return {
    xref: (term) => call("xref", [term]),
    mdn: (query, limit) => call("mdn", limit ? [query, "--limit", String(limit)] : [query]),
    resolve: (url) => call("resolve", [url]),
    blame: (url) => call("blame", [url]),
    irc: (term, limit) => call("irc", limit ? [term, "--limit", String(limit)] : [term]),
    repo: (url) => call("repo", [url]),
  };
}

// Named export for environments that support `import`; the bare function is
// enough for codemode (paste the body, call `makeArcheologist()`).
if (typeof module !== "undefined") module.exports = { makeArcheologist };
