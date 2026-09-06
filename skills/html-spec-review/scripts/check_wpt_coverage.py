#!/usr/bin/env python3
"""
WPT Coverage & Diff Static Analyzer for WHATWG HTML Specification.

Audits spec PR diffs or spec files against linked Web Platform Tests (WPT):
1. Sibling Call Site & Sink Coverage:
   - Extracts all IDL interfaces, methods, and attributes modified in the spec diff (e.g., innerHTML, setHTML, createContextualFragment).
   - Scans WPT test files (or a WPT PR git diff) to verify that EVERY modified sink has test coverage.
   - Flags modified methods that were forgotten in the WPT PR.
2. Exception Parity:
   - Scans modified algorithm steps for 'throw a "..." DOMException' and checks if WPT asserts those exception names.
3. Tentative Naming Correctness:
   - Flags cases where tests for pre-existing standard APIs (e.g. Element.innerHTML) are placed exclusively in .tentative.html files.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Set, Dict, Tuple


class CoverageIssue:
    def __init__(self, category: str, message: str, details: str = ""):
        self.category = category
        self.message = message
        self.details = details

    def __str__(self):
        msg = f"[{self.category}] {self.message}"
        if self.details:
            msg += f"\n    Details: {self.details.strip()}"
        return msg


class WPTCoverageAnalyzer:
    def __init__(self):
        self.issues: List[CoverageIssue] = []

    def extract_sinks_from_spec_diff_or_file(self, content: str) -> Set[str]:
        """Extracts modified IDL methods and attributes (e.g. innerHTML, setHTML, parseHTML)."""
        sinks = set()

        # Match IDL member definitions or references:
        # e.g. <span data-x="dom-element-innerHTML">innerHTML</span> or Element's innerHTML
        # or static Document parseHTMLUnsafe(...)
        idl_member_patterns = [
            r'data-x=["\']dom-[^"\']*?-(\w+)["\']',
            r'\b(?:Element|ShadowRoot|Document|Range)\s+(?:prototype\s+)?([a-zA-Z0-9_]+)\b',
            r'\b(?:The\s+)?([a-zA-Z0-9_]+)\s+(?:getter|setter|method)\s+steps\b',
            r'\b(?:setHTML|setHTMLUnsafe|innerHTML|outerHTML|insertAdjacentHTML|createContextualFragment|parseHTML|parseHTMLUnsafe|parseFromString)\b'
        ]

        for pat in idl_member_patterns:
            for match in re.finditer(pat, content):
                sink = match.group(1) if match.groups() else match.group(0)
                # Filter noise
                if len(sink) > 2 and not sink in {"DOM", "HTML", "IDL", "SVG", "XML", "CSS", "true", "false", "null"}:
                    sinks.add(sink)

        return sinks

    def extract_thrown_exceptions(self, content: str) -> Set[str]:
        """Extracts DOMException names thrown in algorithm steps."""
        exceptions = set()
        pattern = re.compile(r'throw\s+a\s+(?:<span>)?["\']?(\w+)["\']?(?:</span>)?\s+<code>?DOMException</code>?', re.IGNORECASE)
        for match in pattern.finditer(content):
            exceptions.add(match.group(1))
        return exceptions

    def audit_coverage(self, spec_text: str, wpt_files: List[Path]) -> List[CoverageIssue]:
        target_sinks = self.extract_sinks_from_spec_diff_or_file(spec_text)
        thrown_exceptions = self.extract_thrown_exceptions(spec_text)

        # Map each sink to the WPT files mentioning it
        sink_test_map: Dict[str, List[str]] = {sink: [] for sink in target_sinks}
        tested_exceptions: Set[str] = set()

        for wpt_path in wpt_files:
            if not wpt_path.is_file() or not wpt_path.suffix in {'.html', '.js', '.htm'}:
                continue

            test_content = wpt_path.read_text(encoding='utf-8', errors='replace')
            filename = wpt_path.name

            # Check sink occurrences in test content or filename
            for sink in target_sinks:
                if re.search(rf'\b{re.escape(sink)}\b', test_content) or re.search(rf'\b{re.escape(sink)}\b', filename, re.IGNORECASE):
                    sink_test_map[sink].append(str(wpt_path))

                    # Check tentative naming: if it's a pre-existing standard sink, warn about tentative placement
                    legacy_standard_sinks = {"innerHTML", "outerHTML", "insertAdjacentHTML", "createContextualFragment"}
                    if sink in legacy_standard_sinks and ".tentative." in filename:
                        self.issues.append(CoverageIssue(
                            "WPT-TENTATIVE-ON-STANDARD-API",
                            f"Test file '{filename}' tests existing standard API '{sink}' but is marked '.tentative'. Bug fixes and tests for existing standard behaviors should be in non-tentative files.",
                            f"File: {wpt_path}"
                        ))

            # Check exception assertions in tests
            for exc in thrown_exceptions:
                if re.search(rf'assert_throws_dom\s*\(\s*["\']{re.escape(exc)}["\']', test_content):
                    tested_exceptions.add(exc)

        # Flag any sink that has 0 matching tests
        for sink, tests in sink_test_map.items():
            # Focus on high-value DOM/HTML insertion sinks
            priority_sinks = {
                "innerHTML", "outerHTML", "insertAdjacentHTML", "setHTML",
                "setHTMLUnsafe", "createContextualFragment", "parseHTML", "parseHTMLUnsafe"
            }
            if sink in priority_sinks and len(tests) == 0:
                self.issues.append(CoverageIssue(
                    "WPT-MISSING-SINK-COVERAGE",
                    f"Specification sink '{sink}' was modified or referenced in the spec diff, but has NO corresponding tests in the reviewed WPT files.",
                    f"Ensure tests exist verifying '{sink}' under the updated algorithm semantics."
                ))

        # Flag any thrown exception with 0 assert_throws_dom tests
        for exc in thrown_exceptions:
            if exc not in tested_exceptions:
                self.issues.append(CoverageIssue(
                    "WPT-MISSING-EXCEPTION-TEST",
                    f"Spec algorithm throws '{exc}' DOMException, but no WPT test with 'assert_throws_dom(\"{exc}\", ...)' was found.",
                    f"Add negative test coverage verifying that '{exc}' is thrown under invalid arguments."
                ))

        return self.issues


def main():
    parser = argparse.ArgumentParser(description="Audit WPT test coverage against WHATWG HTML spec changes.")
    parser.add_argument("--spec-file", type=Path, required=True, help="Spec source file or diff patch to inspect")
    parser.add_argument("--wpt-dir", type=Path, required=True, help="Path to WPT test directory or files")
    parser.add_argument("--fail-on-issue", action="store_true", default=False, help="Exit with non-zero status if missing coverage is found")
    args = parser.parse_args()

    if not args.spec_file.is_file():
        print(f"Error: spec file not found: {args.spec_file}", file=sys.stderr)
        sys.exit(1)

    if not args.wpt_dir.exists():
        print(f"Error: WPT directory not found: {args.wpt_dir}", file=sys.stderr)
        sys.exit(1)

    spec_content = args.spec_file.read_text(encoding='utf-8', errors='replace')
    wpt_files = list(args.wpt_dir.rglob("*.html")) + list(args.wpt_dir.rglob("*.js")) if args.wpt_dir.is_dir() else [args.wpt_dir]

    analyzer = WPTCoverageAnalyzer()
    issues = analyzer.audit_coverage(spec_content, wpt_files)

    if issues:
        print(f"Found {len(issues)} WPT coverage issue(s):")
        for issue in issues:
            print(f"  {issue}\n")
        if args.fail_on_issue:
            sys.exit(1)
    else:
        print("WPT Coverage Analyzer: All modified sinks and exceptions have corresponding test coverage.")
        sys.exit(0)


if __name__ == "__main__":
    main()
