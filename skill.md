# Agent Skill: Web Standards Archeologist (Paper Trail)

This skill enables the agent to trace any clause, element, algorithm, or GitHub issue/PR in Web Standards (WHATWG, W3C, WICG, IETF) back to its historical origins.

## 1. Protocol
The agent MUST use the `archeologist` tool to bridge the gap between modern spec URLs and historical discussions.

- **Fast Discovery**: Use `--fast` to use `git log -S` (Pickaxe) instead of `log -L`.
- **IETF Support**: Handles RFCs and HTTP drafts by mapping to the `httpwg/http-extensions` repository.

## 2. Advanced Capabilities
- **Editor Intent Detection**: Categorizes changes as "Editorial", "Normative", "Tree Construction", etc.
- **Resolution Mapping**: Extracts "Resolution:" text from commit messages.
- **WPT Correlation**: Automatically generates search links for associated Web Platform Tests.
- **Cross-Standard Archeology**: Seamlessly trace history across HTML, Fetch, CSS, DOM, and HTTP.

## 3. Usage
```bash
archeologist [--fast] [--json] <input>
```

### Examples
```bash
# Trace a WHATWG fragment
archeologist --fast "https://html.spec.whatwg.org/#the-insertion-mode"

# Trace an IETF RFC (Early Hints)
archeologist --fast "https://httpwg.org/specs/rfc8297.html"

# Trace a Fetch algorithm
archeologist --fast "https://fetch.spec.whatwg.org/#process-early-hints-response"
```

## 4. Investigative Strategy
1. Obtain the URL or fragment.
2. Run the archeologist tool to get the commit history.
3. For IETF/HTTP, the tool will search Markdown or XML source files.
4. Review commit messages for rationale, Resolutions, and WPT links.
5. Summarize the "Why" based on the consolidated evidence across standards.
