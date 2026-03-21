#!/usr/bin/env python3
"""
Web Standards Archeologist
Traces spec prose back to its historical "Why".
Supports WHATWG, W3C, WICG, and IETF (HTTPWG).
"""
import os
import re
import subprocess
import sys
import json
from urllib.parse import urlparse

# Cache directory for spec repositories
CACHE_DIR = os.path.expanduser("~/.gemini/cache/specs")

# Mapping of spec domains to GitHub repositories
DOMAIN_REPO_MAP = {
    "html.spec.whatwg.org": "whatwg/html",
    "dom.spec.whatwg.org": "whatwg/dom",
    "fetch.spec.whatwg.org": "whatwg/fetch",
    "url.spec.whatwg.org": "whatwg/url",
    "xhr.spec.whatwg.org": "whatwg/xhr",
    "infra.spec.whatwg.org": "whatwg/infra",
    "encoding.spec.whatwg.org": "whatwg/encoding",
    "mimesniff.spec.whatwg.org": "whatwg/mimesniff",
    "storage.spec.whatwg.org": "whatwg/storage",
    "notifications.spec.whatwg.org": "whatwg/notifications",
    "fullscreen.spec.whatwg.org": "whatwg/fullscreen",
    "console.spec.whatwg.org": "whatwg/console",
    "compat.spec.whatwg.org": "whatwg/compat",
    "quirks.spec.whatwg.org": "whatwg/quirks",
    "drafts.csswg.org": "w3c/csswg-drafts",
    "drafts.fxtf.org": "w3c/fxtf-drafts",
    "drafts.css-houdini.org": "w3c/css-houdini-drafts",
    "svgwg.org": "w3c/svgwg",
    "httpwg.org": "httpwg/http-extensions",
    "datatracker.ietf.org": "httpwg/http-extensions", 
}

def log(msg, use_json=False):
    if not use_json:
        print(f"[*] {msg}", file=sys.stderr)

def get_repo_for_url(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Check direct mapping
    if domain in DOMAIN_REPO_MAP:
        repo_name = DOMAIN_REPO_MAP[domain]
        return f"https://github.com/{repo_name}.git", repo_name

    # GitHub Issue/PR/Repo URL
    if domain == "github.com":
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2:
            repo_name = f"{parts[0]}/{parts[1]}"
            return f"https://github.com/{repo_name}.git", repo_name

    # WICG
    if "wicg.github.io" in domain:
        repo_name = parsed.path.strip("/").split("/")
        if len(repo_name) > 1:
            repo_name = repo_name[1]
            return f"https://github.com/WICG/{repo_name}.git", f"WICG/{repo_name}"
    
    # IETF/RFCs - Heuristic for HTTP extensions
    if "ietf.org" in domain or "httpwg.org" in domain:
        if "/rfc8297" in parsed.path or "early-hints" in parsed.path:
            return "https://github.com/httpwg/http-extensions.git", "httpwg/http-extensions"

    return None, None

def ensure_repo(repo_url, repo_name, use_json=False):
    target_dir = os.path.join(CACHE_DIR, repo_name.replace("/", "-"))
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)
    if not os.path.exists(target_dir):
        log(f"Cloning {repo_url} into cache...", use_json)
        # Use depth 1000 for efficiency but still enough history
        subprocess.check_call(["git", "clone", "--depth", "1000", repo_url, target_dir])
    return target_dir

def find_source_file(repo_path, fragment, url=None, use_json=False):
    log(f"Searching for source file containing '{fragment}'...", use_json)
    if "whatwg-html" in repo_path:
        return os.path.join(repo_path, "source")
    
    # IETF / HTTPWG
    if "httpwg-http-extensions" in repo_path:
        if url:
            rfc_match = re.search(r"rfc(\d+)", url)
            if rfc_match:
                rfc_num = rfc_match.group(1)
                try:
                    output = subprocess.check_output(["find", repo_path, "-name", f"*{rfc_num}*"], text=True)
                    if output: return output.split("\n")[0].strip()
                except: pass
        try:
            output = subprocess.check_output(["grep", "-rl", fragment, repo_path, "--include=*.md", "--include=*.xml"], text=True)
            return output.split("\n")[0].strip()
        except: pass

    # CSSWG / Bikeshed
    if "csswg-drafts" in repo_path and url:
        spec_path = urlparse(url).path.strip("/")
        if spec_path:
            full_path = os.path.join(repo_path, spec_path)
            if os.path.exists(full_path):
                for f in os.listdir(full_path):
                    if f.endswith(".bs"):
                        return os.path.join(full_path, f)

    # General search for fragment ID
    patterns = [
        f'id=["\']?{re.escape(fragment)}["\']?',
        f'{{#{re.escape(fragment)}}}', 
        f'anchor: {re.escape(fragment)}', 
    ]
    for p in patterns:
        try:
            output = subprocess.check_output([
                "grep", "-rlE", p, repo_path, 
                "--include=*.bs", "--include=source", "--include=*.html", "--include=*.md", "--include=*.xml"
            ], text=True)
            return output.split("\n")[0].strip()
        except:
            continue

    for f in ["index.bs", "Overview.bs", "source", "dom.bs", "fetch.bs", "index.html", "README.md"]:
        path = os.path.join(repo_path, f)
        if os.path.exists(path):
            return path
    return None

def get_line_for_fragment(source_file, fragment, use_json=False):
    log(f"Mapping fragment to line number in {os.path.basename(source_file)}...", use_json)
    patterns = [
        rf'id=["\']?{re.escape(fragment)}["\']?\b',
        rf'data-x=["\']?{re.escape(fragment)}["\']?\b',
        rf'\{{#{re.escape(fragment)}\}}',
    ]
    for pattern in patterns:
        try:
            output = subprocess.check_output(["grep", "-nE", pattern, source_file], text=True)
            return int(output.split(":")[0])
        except:
            pass

    words = fragment.split("-")
    search_words = [w for w in words if len(w) > 2] or words
    pattern = ".*".join(re.escape(w) for w in search_words)
    try:
        output = subprocess.check_output(["grep", "-niE", f"(<h[1-6]|<dfn|Name:|# ).*{pattern}", source_file], text=True)
        return int(output.split(":")[0])
    except:
        pass

    # Fallback for multi-line: search for the last word in a header/dfn
    if len(search_words) > 1:
        last_word = search_words[-1]
        try:
            # Use word boundaries for the last word to avoid partial matches like "Helper"
            output = subprocess.check_output(["grep", "-niE", f"(<h[1-6]|<dfn|Name:|# ).*\\b{re.escape(last_word)}\\b", source_file], text=True)
            for line_match in output.split("\n"):
                if not line_match.strip(): continue
                ln = int(line_match.split(":")[0])
                try:
                    # Look for preceding words in the same line or previous lines
                    context = subprocess.check_output(["sed", "-n", f"{max(1, ln-2)},{ln}p", source_file], text=True).lower()
                    if any(w.lower() in context for w in search_words[:-1]):
                        return ln
                except: pass
            return int(output.split(":")[0])
        except:
            pass

    return None

def trace_history(repo_path, source_file, line, fast=False, use_json=False):
    rel_source = os.path.relpath(source_file, repo_path)
    if fast:
        log(f"Performing fast Pickaxe search for content of line {line}...", use_json)
        try:
            blame = subprocess.check_output([
                "git", "-C", repo_path, "blame", "-L", f"{line},{line}", rel_source, "--porcelain"
            ], text=True)
            sha = blame.split("\n")[0].split(" ")[0]
            content = subprocess.check_output(["sed", "-n", f"{line}p", source_file], text=True).strip()
            if content:
                pickaxe = subprocess.check_output([
                    "git", "-C", repo_path, "log", "-S", content, "--oneline", "--reverse", rel_source
                ], text=True)
                first_sha = pickaxe.split("\n")[0].split(" ")[0]
                return subprocess.check_output([
                    "git", "-C", repo_path, "show", "-s", "--pretty=format:%H%n%an%n%ad%n%s%n%b%n---END---", first_sha
                ], text=True)
        except:
            pass

    log(f"Performing deep line-trace history for line {line} (this may take a moment)...", use_json)
    try:
        output = subprocess.check_output([
            "git", "-C", repo_path, "log", 
            f"-L {line},{line}:{rel_source}", 
            "--no-patch", 
            "--pretty=format:%H%n%an%n%ad%n%s%n%b%n---END---"
        ], text=True)
        return output
    except:
        return None

def find_commits_for_issue(repo_path, issue_id, use_json=False):
    log(f"Searching for commits referencing issue #{issue_id}...", use_json)
    try:
        pattern = f"#{issue_id}\\b"
        output = subprocess.check_output([
            "git", "-C", repo_path, "log", 
            f"--grep={pattern}", 
            "--pretty=format:%H%n%an%n%ad%n%s%n%b%n---END---"
        ], text=True)
        return output
    except:
        return None

def extract_links(text):
    links = []
    # GitHub Issues/PRs
    gh_matches = re.findall(r"(?:#|whatwg/html#|w3c/csswg-drafts#|WICG/[^/]+#|httpwg/[^/]+#)(\d+)", text)
    for m in gh_matches:
        links.append({"type": "GitHub Issue", "url": f"GH#{m}"})
        links.append({"type": "WPT Search", "url": f"https://github.com/web-platform-tests/wpt/search?q={m}"})
    
    # URLs
    urls = re.findall(r"https?://[^\s\)\(]+", text)
    for u in urls:
        label = "Link"
        if "github.com" in u: label = "GitHub"
        elif "w3.org/Bugs" in u: label = "Bugzilla"
        elif "lists.w3.org" in u: label = "Mailing List"
        elif "crbug.com" in u: label = "Chromium"
        elif "ietf.org" in u: label = "IETF"
        links.append({"type": label, "url": u})

    if "Resolution:" in text or "RESOLVED:" in text:
        res_matches = re.findall(r"(?:Resolution|RESOLVED):?\s*(.+)", text)
        for m in res_matches:
            links.append({"type": "Resolution", "url": m.strip()})

    svn_matches = re.findall(r"git-svn-id: .*@(\d+)", text)
    for m in svn_matches:
        links.append({"type": "W3C Discussion", "url": f"https://www.google.com/search?q=site:lists.w3.org+r{m}"})
        
    return links

def detect_intent(summary):
    codes = {"[e]": "Editorial", "[ct]": "Tree Construction", "[c]": "Conformance", "[giow]": "General", "[a]": "Authoring"}
    for code, label in codes.items():
        if code in summary: return label
    return "Normative" if not summary.lower().startswith("editorial") else "Editorial"

def parse_history(history_output):
    if not history_output: return []
    commits = history_output.split("---END---")
    parsed_commits = []
    for commit in commits:
        commit_text = commit.strip()
        if not commit_text: continue
        lines = commit_text.split("\n")
        if len(lines) < 4: continue
        sha, author, date, summary = lines[0], lines[1], lines[2], lines[3]
        body = "\n".join(lines[4:])
        links = extract_links(summary + "\n" + body)
        intent = detect_intent(summary)
        parsed_commits.append({"sha": sha, "author": author, "date": date, "summary": summary, "links": links, "intent": intent})
    return parsed_commits

def main():
    use_json = "--json" in sys.argv
    fast_mode = "--fast" in sys.argv
    args = [a for a in sys.argv[1:] if a not in ["--json", "--fast"]]

    if not args:
        print("Usage: archeologist [--json] [--fast] <url, fragment, issue shorthand or commit sha>")
        sys.exit(1)

    input_val = args[0]
    
    if re.match(r"^[0-9a-f]{7,40}$", input_val):
        for d in os.listdir(CACHE_DIR):
            repo_path = os.path.join(CACHE_DIR, d)
            if not os.path.isdir(os.path.join(repo_path, ".git")): continue
            try:
                output = subprocess.check_output([
                    "git", "-C", repo_path, "show", "-s", 
                    "--pretty=format:%H%n%an%n%ad%n%s%n%b%n---END---", 
                    input_val
                ], text=True)
                commits = parse_history(output)
                if use_json:
                    print(json.dumps(commits, indent=2))
                else:
                    for commit in commits:
                        print(f"[{commit['intent']}] {commit['sha'][:10]} by {commit['author']}")
                        print(f"Summary: {commit['summary']}")
                        for link in commit['links']:
                            print(f"  - {link['type']}: {link['url']}")
                sys.exit(0)
            except:
                continue
        sys.exit(1)

    issue_match = re.match(r"^(?:([^/]+)/)?([^#]+)#(\d+)$", input_val)
    if issue_match:
        org, repo, issue_id = issue_match.groups()
        repo_name = f"{org or 'whatwg'}/{repo}"
        repo_path = ensure_repo(f"https://github.com/{repo_name}.git", repo_name, use_json)
        history = find_commits_for_issue(repo_path, issue_id, use_json)
        commits = parse_history(history)
        if use_json:
            print(json.dumps({"repo": repo_name, "issue": issue_id, "commits": commits}, indent=2))
        else:
            for c in commits:
                print(f"[{c['intent']}] {c['sha'][:8]} {c['summary']}")
                for l in c['links']: print(f"  - {l['type']}: {l['url']}")
        sys.exit(0)

    repo_url, repo_name = get_repo_for_url(input_val)
    if not repo_url:
        repo_url, repo_name = "https://github.com/whatwg/html.git", "whatwg/html"
        fragment = input_val.split("#")[-1]
    else:
        fragment = urlparse(input_val).fragment or input_val.split("#")[-1]

    repo_path = ensure_repo(repo_url, repo_name, use_json)
    source_file = find_source_file(repo_path, fragment, url=(input_val if "http" in input_val else None), use_json=use_json)
    if not source_file:
        if not use_json:
            print(f"Error: Could not find source file for {fragment} in {repo_path}")
        sys.exit(1)

    line = get_line_for_fragment(source_file, fragment, use_json)
    if not line:
        if not use_json:
            print(f"Error: Could not find line for {fragment} in {source_file}")
        sys.exit(1)

    history = trace_history(repo_path, source_file, line, fast=fast_mode, use_json=use_json)
    commits = parse_history(history)
    
    if use_json:
        print(json.dumps({"repo": repo_name, "commits": commits}, indent=2))
    else:
        print(f"Archeological Trail for {repo_name} -> {os.path.basename(source_file)}:L{line}\n")
        for c in commits:
            print(f"[{c['intent']}] {c['sha'][:8]} {c['summary']} ({c['date']})")
            for l in c['links']:
                print(f"  - {l['type']}: {l['url']}")
            print("-" * 20)

if __name__ == "__main__":
    main()
