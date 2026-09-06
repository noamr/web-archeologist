---
name: html-spec-review
description: Comprehensive guidelines for writing, editing, and reviewing the WHATWG HTML standard. Enforces style, Web IDL rules, algorithmic correctness, mutation lifecycle, parser edge cases, and developer's edition annotations.
---

# Agent Skill: HTML Specification Writing and Review Guide

> **Note on Extended Guidelines:**
> For broader guidance on substantive architectural judgment (including threading models, backwards compatibility, API design consistency, and state encapsulation) across W3C, WHATWG, and WICG specifications, as well as additional Bikeshed/Wattsi syntax rules, please refer to the external [spec-writing-skill repository](https://github.com/domfarolino/spec-writing-skill).

This skill provides the official guidelines, prose style conventions, algorithmic requirements, and structural review principles for writing, editing, and reviewing the WHATWG HTML standard.

Refer to this skill when authoring spec text, reviewing pull requests, or conducting rigorous self-reviews to prevent common failure modes that pass automated syntax checks (Wattsi/Bikeshed) but introduce critical logical, security, or architectural regressions.

---

## 1. Web IDL Rules & Cross-References

### 1.1. Cross-references inside `<pre class="idl">`
- In Web IDL blocks (`<pre class="idl">`), cross-references MUST use `<span>`, NEVER `<code>`.
- Web IDL syntax is already preformatted as code. Using `<code>` creates nested markup that violates WHATWG style and triggers reviewer objections.
  - *Correct*: `static <span>Document</span> <span data-x="dom-parseHTMLUnsafe">parseHTMLUnsafe</span>((<span>TrustedHTML</span> or DOMString) html, optional (<span>ParseHTMLUnsafeOptions</span> or <span>TrustedParserOptions</span>) options = {});`
  - *Incorrect*: `static <span>Document</span> ... optional (<code data-x="tt-trustedparseroptions">TrustedParserOptions</code>) options = {});`

### 1.2. Dictionaries Become Untyped Infra Maps (No "is a Dictionary" in Algorithms)
- Once an IDL dictionary argument passes the Web IDL conversion boundary into algorithm prose, it is converted into an **Infra ordered map** of strings to values.
- **It does NOT retain any type tag, branding, or record of which dictionary type it came from.**
- **Anti-Pattern**:
  - *Never write*: `If <var>options</var> is a <code>SetHTMLUnsafeOptions</code>:`
  - *Never write*: `If <var>options</var> is a dictionary:`
- **Correct Pattern**:
  - Check member existence on the map: `If <var>options</var>["<code data-x="dom-SetHTMLUnsafeOptions-runScripts">runScripts</code>"] <span data-x="map exists">exists</span>:` or use map fallback: `<var>options</var>["runScripts"] <span data-x="map with default">with default</span> false`.
  - Only platform objects / interfaces (e.g. `TrustedParserOptions`, `Node`, `Element`) retain type identity and can be checked with `If <var>x</var> is an <span>InterfaceName</span>:`.

### 1.3. Web IDL Optional Arguments & Dictionary Defaults
- If an optional dictionary parameter has **no required members**, it MUST specify `= {}` in its IDL declaration:
  - *Correct*: `optional ParseHTMLOptions options = {};`
  - *Incorrect*: `optional ParseHTMLOptions options;`
- **Variadic Parameters**:
  - A trailing variadic argument (`any... arguments`) forces the preceding parameter to be optional in Web IDL.

### 1.4. Formatting IDL Members
- Every attribute, constant, and operation must be on its own line.
- Do not wrap parameter names or type names in `<var>` tags within IDL blocks.

---

## 2. Algorithms, Variable Lifecycle & Scope

### 2.1. Variable Lifecycle: Strict "Let" vs. "Set"
- **First declaration**: MUST use **"Let `<var>x</var>` be `<var>y</var>`"**.
- **Reassignment / Mutation**: MUST use **"Set `<var>x</var>` to `<var>y</var>`"**.
- **Failure Modes to Catch**:
  1. Using `Set <var>x</var> to ...` when `<var>x</var>` was never declared with `Let`.
  2. Re-declaring a variable with `Let <var>x</var> be ...` in the same algorithm scope.
  3. **Dead initializations**: Declaring `Let <var>x</var> be null` immediately before an exhaustive `If/Else` or `switch` block where every branch assigns `<var>x</var>`.

### 2.2. Dangling Antecedents & Variable Reassignment
- If a variable is mutated or reassigned, never refer to "the original `<var>x</var>`" in later steps unless explicitly preserved:
  - *Correct*: `Let <var>originalContext</var> be <var>context</var>.` ... `Set <var>context</var> to ...` ... `Use <var>originalContext</var>.`
  - *Incorrect*: Reassigning `<var>context</var>` and then later referring to "the original context".

### 2.3. Algorithm Container & Scoping
- Wrap every algorithm in `<div algorithm>`. The preamble (name, arguments, return type) goes inside the `<div>`. Do not indent algorithm container contents.
- Multi-algorithm scopes can use `<div var-scope>`. If a variable is only referenced once, mark it `<var ignore>x</var>`.
- Use the "initially" pattern: "...initially null", "...initially false", "...initially the empty list « »".

### 2.4. Phrasing Conventions
- Use standard Infra conjugation: `the result of <span data-x="...">getting the popcorn</span> given <var>args</var>` (not "the result of calling get the popcorn with...").
- Assertions: `<span>Assert</span>: <var>x</var> is non-null.` (Always wrap in `<span>Assert</span>:`, never bare `Assert:`).
- Context: `<span>this</span>` (never bare "this").

### 2.5. Scope Leaks & Branch-Bound Variables (`ALGO-UNBOUND-VAR-OUTER-SCOPE`)
- **Blocker Bug**: Declaring a variable with `Let <var>x</var> be` inside a nested conditional sub-list (`<ol>`) and subsequently reading `<var>x</var>` at the outer algorithm scope or in an `Otherwise` branch.
  - On any execution path where the conditional branch does not run, `<var>x</var>` is completely unbound and dereferencing it creates an invalid specification state.
- **Rule**:
  - If a variable is read or tested outside a branch, it MUST be initialized at the outer algorithm scope *before* the branching block:
    ```html
    <!-- Correct Pattern -->
    <li><p>Let <var>fetchTimingInfo</var> be null.</p></li>
    <li><p>If <var>navigationParams</var>'s fetch controller is not null:</p>
     <ol>
      <li><p>Set <var>fetchTimingInfo</var> to the result of extracting the full timing info...</p></li>
     </ol>
    </li>
    ...
    <li><p>If <var>fetchTimingInfo</var> is not null:</p>...</li>
    ```

### 2.6. Unused Variables & Argument Renaming (`ALGO-UNUSED-VAR`)
- Every variable introduced with `Let <var>x</var> be` must be referenced in subsequent steps.
- **Refactoring Hazard**:
  - When refactoring algorithm signatures or renaming parameters (e.g., replacing `context` with `target`), authors frequently introduce the new parameter but leave dangling references to the old name or create dead intermediate bindings.
  - Always audit the entire algorithm to ensure the old variable name is not referenced and the new variable is actually consumed.
  - If a destructured tuple member or parameter is intentionally unused, mark it with `<var ignore>name</var>`.

### 2.7. Infra List Iteration Syntax (`ALGO-LIST-OF`)
- In Infra, iterating over a list, set, or map always uses **"of"**, NEVER "in":
  - *Correct*: `For each <var>node</var> of <var>children</var>:`
  - *Incorrect*: `For each <var>node</var> in <var>children</var>:`

### 2.8. Redundant `data-x` Elimination (`ALGO-REDUNDANT-DATA-X`)
- Wattsi automatically links cross-references when the inner text matches the term definition name (case-insensitively).
- Writing `<span data-x="Foo">Foo</span>` or `<span data-x="set and filter HTML">set and filter HTML</span>` is redundant.
- Omit `data-x` when the text is identical to the target concept: `<span>set and filter HTML</span>`. Keep `data-x` only when the visible text differs from the definition key (e.g. inflections, plurals, or abbreviations).

---

## 3. State Mutation, Aliasing & Temporal Sequencing

### 3.1. The Shallow Clone Trap (`[=map/clone=]`)
- In Infra, `[=map/clone=]` and `[=list/clone=]` are **strictly shallow**. Keys and values are copied into a new collection, but nested maps, lists, sets, and objects are **referenced, not copied**.
- If a cloned dictionary/map contains nested maps (e.g. `SanitizerConfig`'s `elements`, `attributes`, `removeElements`), running in-place mutative algorithms (such as removing entries or modifying nested lists) **directly mutates the original object's internal data structures!**
- **Review Rule**:
  - If a spec guarantees immutability or script-isolation, verify whether values inside the map are mutable objects or nested maps.
  - If nested mutable collections exist, the algorithm must deep-clone, recursively copy, or canonicalize via fresh throwaway instances rather than relying on `[=map/clone=]`.
- **Platform Object Encapsulation**:
  - Never return an internal platform map/dictionary directly by reference from a getter or `[NewObject]` method if script can observe mutations or if subsequent calls expect immutability.

### 3.2. Temporal State Snapshotting (Evaluate Before Tree/Stack Mutation)
- Algorithms that query dynamic parser or DOM state (e.g. `adjusted insertion location`, `current node`, `stack of open elements`, `insertion parent`) MUST capture that state **before** executing steps that mutate the tree or stack.
- **Classic Regression**:
  - Re-evaluating `adjusted insertion location` *after* calling `insert a foreign element` or pushing an element to the stack causes `scope` to resolve to the *new element's own contents* (breaking `<template for>` patching).
- **Review Rule**:
  - Whenever an algorithm inspects tree context, check whether any preceding step in the same sequence added, reparented, or removed elements.
  - If so, the location/parent MUST be captured into a local variable *before* the insertion:
    `Let <var>adjustedInsertionLocation</var> be the <span>appropriate place for inserting a node</span>.`
    `Let <var>scope</var> be <var>adjustedInsertionLocation</var>'s target parent.`
    `Insert the element...`

### 3.3. Post-Construction Local Mutation Bug
- When constructing an object or parser whose initialization takes parameters (e.g., `Create a new HTML parser whose scripting mode is <var>scriptingMode</var>`):
  - Any subsequent mutation of the local variable `<var>scriptingMode</var>` does **NOT** update the parser's stored mode!
- **Review Rule**:
  - Calculate all configuration flags and modes **before** constructing the object, OR explicitly update the object's internal slot afterward.

### 3.4. Atomic Validation before Destructive Mutation
- APIs that perform destructive DOM operations (such as clearing an element's children or removing a node from its parent) MUST perform all option validation, sanitization parsing, and dependency construction **before** mutating the DOM.
- If option validation or parser construction fails and throws an exception, the DOM must remain pristine and unmutated. Never clear or detach nodes before validation can throw!

### 3.5. Pre-Initialization State Access (Unborn Object Capabilities)
- **Failure Mode**: Inspecting permissions policy, environment settings, or cross-origin capabilities on an object *before* its child components, document, or global have been instantiated and linked.
  - *Example (from PR #12890 review)*: Checking `window's relevant settings object's cross-origin isolated capability` before `window` has an associated `Document`. In a newly created Window, its associated document is unset; in a reused `about:blank`, it resolves to the old document's policy rather than the new response's permissions policy!
- **Review Rule**:
  - Audit the lifecycle of objects passed to algorithms. Never query capability getters or policy algorithms on an object until all associated subordinates (`window.document`, `intendedParent`, execution context) are fully linked.
  - If a timestamp or state must be captured early, capture the raw/uncoarsened value (e.g. `unsafeSharedCurrentTime`), and coarsen or convert it *after* the document and its permissions policy are bound.

### 3.6. Fallback & Null Path Auditing on Previously Unconditional Steps
- **Failure Mode**: When turning a previously unconditional algorithm step into a conditional branch (e.g. `If <var>controller</var> is not null:`), the `Otherwise` path is frequently neglected or assumes all inputs are regular network fetches.
  - *Example (from PR #12890 review)*: Restricting navigation timing entry creation to when `navigationParams's fetch controller is not null` caused timing entries to silently disappear for `srcdoc` documents, `javascript:` URLs, UA error pages, and `multipart/x-mixed-replace` continuations.
- **Review Rule**:
  - Whenever an algorithm step is guarded by a non-null condition, explicitly audit and document the behavior for every possible non-fetch or null-controller scenario:
    1. `about:srcdoc` and `about:blank` navigations
    2. `javascript:` URL documents
    3. UA-generated error pages
    4. Navigations supplied with synthetic responses (`<object>`, `<embed>`, multipart)
    5. In-flight aborted traversals (e.g. PR #12846)
  - Ensure the fallback branch creates synthetic fallback structs or documents the intentional omission with matching WPT tests.

---

## 4. HTML Parser, Tree Construction & Edge Cases

### 4.1. The Adoption Agency Algorithm (AAA) Audit
- The Adoption Agency Algorithm (AAA) is the premier source of parser-level corner cases. AAA clones formatting elements, creates elements directly from tokens, moves nodes, and reparents subtrees.
- **Review Checklist for Any Tree-Builder / Sanitization Modification**:
  1. *Token creation bypass*: Does AAA create elements from tokens without going through your new insertion/sanitization algorithm? (Audit AAA steps 4.13.8 and 4.18).
  2. *Parentless `lastNode`*: If nodes are removed or rejected during AAA, can `lastNode` have no parent? Verify `lastNode`'s parent is non-null before calling `remove`, and reset `lastNode` to null.
  3. *Self-ancestor reparenting loops*: Ensure AAA reparenting steps do not attempt to append an element to itself when an inner loop has already moved it.

### 4.2. Speculative Parsing & Preload Scanner Integrity
- Tree-builder behaviors (such as script blocking, sanitization, or custom element delays) must account for speculative HTML parsing.
- If a node or attribute would be removed or blocked by the tree builder, speculative parsing must either sanitize mock elements or be suppressed for that subtree. Otherwise, speculative fetches (e.g. for `<img>`, `<script>`, or `<base>`) will execute over the network before the tree builder removes them.

### 4.3. Direct Root & Body Appends / Attribute Merging
- Not all elements enter the tree through standard element insertion:
  - Initial `<html>` and `<body>` elements may be created and appended through dedicated root creation steps.
  - Duplicate `<html>` and `<body>` start tags in markup **merge attributes directly** into existing open elements without running generic element insertion.
- When adding tree-builder policies (e.g. sanitization, CSP hooks), explicitly audit attribute merging and root creation steps.

### 4.4. `<template>` Target Redirection
- Setting content on an `HTMLTemplateElement` (`innerHTML`, `setHTML`, `streamHTML`, positional insertion) MUST target the template's **`template contents` (`content`)**, NOT the `HTMLTemplateElement` itself.
- **Review Rule**:
  - Use a centralized helper (e.g. "appropriate place for inserting a node" or "HTML insertion target") rather than ad-hoc inline checks at individual API call sites to avoid regressions across sibling methods.

---

## 5. Parallel Call Site Exhaustiveness & Internal Helpers

### 5.1. Exhaustive Sibling Call Site Audit
- When modifying the signature, parameters, or return type of an internal parsing or serialization algorithm (e.g. `fragment parsing algorithm steps`, `set and filter HTML`), you MUST audit **every parallel caller across HTML, DOM, and DOM Parsing specifications**:
  - `Element.prototype.innerHTML` setter
  - `ShadowRoot.prototype.innerHTML` setter
  - `Element.prototype.outerHTML` setter
  - `Element.prototype.insertAdjacentHTML()`
  - `Range.prototype.createContextualFragment()`
  - `DOMParser.prototype.parseFromString()`
  - `Document.parseHTML()` / `Document.parseHTMLUnsafe()`
  - `Element.prototype.setHTML()` / `Element.prototype.setHTMLUnsafe()`
  - `ShadowRoot.prototype.setHTMLUnsafe()`
  - Streaming variants (`streamHTML`, `streamPrependHTML`, etc.)
- A change to `fragment parsing algorithm steps` that only updates `setHTML()` will silently leave `ShadowRoot.innerHTML` or `createContextualFragment()` broken or passing stale arguments.

### 5.2. No Masking Defaults on Core Internal Algorithms
- **Do not add optional parameters with default values to internal abstract algorithms merely to avoid updating existing call sites.**
  - *Example*: Adding `an optional fragment parser mode mode (default Normal)` to `fragment parsing algorithm steps`.
- Defaults silently mask forgotten call sites. Legacy callers (like `outerHTML` or `createContextualFragment`) will pick up the default without explicit author consideration.
- **Rule**: Make parameters mandatory on internal algorithms during refactoring so that omitted call sites fail loudly during spec review and compilation.

### 5.3. Internal Helper Contract & Parameter Typing
- Ensure that helper algorithms and their callers agree on parameter types and order:
  - If a helper expects `(target, html, options, mode)`, do not pass `(html, this, options, safeBoolean)` at call sites.
  - Avoid conflating enums (`Legacy`, `Unsafe`, `Normal`) with boolean flags (`safe`).

---

## 6. Cross-Spec Layering, Sinks & CSP Reporting

### 6.1. No Fabricated or Synthetic Sinks
- Sink names passed to security violation algorithms (Content Security Policy, Trusted Types) MUST correspond to **real, JavaScript-observable API entry points**:
  - *Valid sinks*: `"Element innerHTML"`, `"ShadowRoot innerHTML"`, `"Document parseHTMLUnsafe"`, `"Range createContextualFragment"`.
  - *Invalid synthetic sinks*: `"Sanitizer"`, `"HTMLParser"`, `"FragmentParser"`.
- Passing synthetic sink names causes sample reports and developer console errors to report nonsensical entries like `"Sanitizer|"`.

### 6.2. Cross-Spec Sentinels vs. String Literals
- If a dependency specification defines a sentinel value (e.g., the `Stream` sentinel in Trusted Types), pass the actual sentinel object/record across the spec boundary.
- Do NOT pass string literals like `"Stream"`. String literals trigger string conversion paths (e.g. running `createHTML` on the word "Stream") instead of selecting sentinel dispatch branches.

### 6.3. Layering & Clean Inversion
- Core HTML tree-construction and fragment-parsing algorithms should remain agnostic of external subsystems where possible. Subsystems (such as CSP) should define integration hooks into HTML rather than HTML reaching directly into subsystem algorithms.

---

## 7. Formatting and Markup Rules

### 7.1. Line Wrapping
- Strictly wrap lines at **100 characters**.
- Attributes or their values can contain newlines to respect this.
- Do not insert newlines between inline tag names and text if it inserts unwanted spaces (e.g., `<i data-x="...">\ntext</i>` is incorrect).

### 7.2. Lists (`<ol>`, `<ul>`, `<li>`, `<dt>`, `<dd>`)
- Every `<li>` must wrap its text content in a `<p>` (except in `<ul class="brief">`).
- Format as `<li><p>Text</p></li>` on the same line if possible, or indent nested blocks.
- Separate consecutive list items with a blank line. Do not put blank lines at the list's absolute start/end.
- Indentation uses a single space per block nesting level:
  - For top-level lists, `<ol>` is indented by 2 spaces, and `<li>` is indented by 3 spaces.
  - Wrapped lines within `<li><p>...</p></li>` match the indentation of the line (3 spaces for top-level list items).
  - Nested block elements (`<p>`, `<ul>`, `<ol>`) starting on their own line inside `<li>` are indented by 1 space relative to the parent `<li>`.
- **Brief Lists (`<ul class="brief">`)**: Use for simple/short lists. Items must **not** wrap content in a `<p>` tag. No blank lines between items.
- **Switch Lists (`<dl class="switch">`)**: Use for complex branch logic. Sibling `<dt>` conditions map to a single `<dd>` consequence/action.

### 7.3. Tags and Quotation
- Always use double quotes for attributes.
- Never omit end tags (always close all `<p>`, `<li>`, `<dt>`, and `<dd>` tags).
- No newline before `>` in closing tags: write `>attribute</code>` not `\n>attribute</code>`.

---

## 8. Prose Style, Grammar and Conventions

### 8.1. Conditional Statements
- **Inline consequence**: Use the full **"If [condition], then [consequence]"** structure (e.g., "If <var>x</var> is true, **then** return.").
- **Block/Sub-list consequence**: Omit "**then**" and end with a colon (e.g., "If <var>x</var> is true:" followed by a nested list).
- **Multiple conditions (more than two)**: Use **"If any of the following are true:"** or **"If all of the following are true:"**, followed by a `<ul>` containing conditions, with the consequence in a subsequent `<p>` starting with "then...". Do not chain multiple "or" clauses in inline prose.

### 8.2. Branching & Fallbacks ("otherwise")
- **Subsequent branches**: "Otherwise, if [condition], [consequence]." (No "then" keyword).
- **Fallback branch**: Use a simple "**Otherwise, [consequence]**" or "**Otherwise:**". Do not repeat negative conditions from previous branches.
- **Inline Ternary**: Use the format: `[value1] if [condition]; otherwise [value2]` (note the semicolon before `otherwise`).

### 8.3. Antonym and Negative Concept Linking
- When setting boolean flags or checking disabled states, link to the explicit negative definition rather than linking the negative phrase to the positive definition.
- *Example*: `concept-n-script` defines "scripting is enabled", whereas `concept-n-noscript` defines "scripting is disabled".
  - *Correct*: `Set <var>parser</var>'s <span>parser scripting disabled</span> to true if <span data-x="concept-n-noscript">scripting is disabled</span> for <var>document</var>; otherwise false.`

### 8.4. Enums, Actions, and State Values
- **Web IDL Enums**: Defined as `"butt"`. Reference in prose as `"<code data-x="">butt</code>"`.
- **Defined Actions**: Defined as `<dfn data-x="...">"Remove"</dfn>`. Reference as `<span data-x="...">"Remove"</span>`.
- **States & Modes**: Capitalize exactly as defined in their definition (e.g., `<span>Disabled</span>`).

### 8.5. Standard Namespaces Casing
- All standard namespace cross-references use lowercase `"namespace"`:
  - `<span>HTML namespace</span>`
  - `<span>SVG namespace</span>`
  - `<span>MathML namespace</span>` (never `<span>MathML Namespace</span>`)
  - `<span>XML namespace</span>`, `<span>XLink namespace</span>`, `<span>XMLNS namespace</span>`

### 8.6. General Conventions
- Omit "the string" prefix before string literals (e.g., "match for `<code data-x="">text/html</code>`").
- Navigation & Exit: Use "return" or "return <var>value</var>" for entire algorithms; "abort these steps" for sub-steps or parallel sequences.
- Use American English (`behavior`, `color`) and Oxford commas in listings.

### 8.7. Grammatical Conjunctions on Item Removal
- When removing an item from a comma-separated list of items in prose (e.g. deleting an obsolete property or concept from an enumeration like "The encoding, mode, custom element registry, and allow declarative shadow roots"):
  - Verify that the coordinating conjunction ("and" or "or") is preserved and correctly placed before the new final item.
  - Deleting the trailing item without moving "and" to the preceding item creates an ungrammatical sentence (e.g. "The encoding, mode, custom element registry.").

---

## 9. Infra Data Structures and Iteration

- **Lists**:
  - Literal: `Let <var>list</var> be « "a", "b" ».`
  - Destructuring: `Let « <var>a</var>, <var>b</var> » be <var>list</var>.`
  - Access & Size: Zero-based index `list[0]` and `size` (never `length` or `count`).
  - Verbs: `append`, `extend A with B`, `prepend`, `replace ... within ...`, `insert ... into ... before [index]`, `remove ... from ...`, `contains`, `is empty`.
- **Maps**:
  - Literal: `Let <var>map</var> be «[ "a" → 1 ]».` (right arrow `→`).
  - Access & Default: `map["key"]` or `map["key"] with default 0`. Check existence with `exists`.
  - Verbs: `set map[key] to value`, `remove map[key]`, `clear map`, `get the keys`, `get the values`, `map's size`.
- **Structs & Tuples**:
  - Struct: `Let <var>x</var> be a struct whose property is value.`
  - Tuple: `Let <var>x</var> be (value1, value2).` Access by field name or index (`x[0]`).
- **Loops**:
  - For each: `For each <var>item</var> of <var>items</var>:` (use **of**, not in).
  - Map entries: `For each <var>key</var> → <var>value</var> of <var>map</var>:`
  - While: `While [condition]:`. Control with `continue` and `break`.

---

## 10. Writing domintro Blocks, Notes & Warnings

`<dl class="domintro">` provides developer-friendly Web IDL explanations (IDL and normative steps are hidden in the Developer's Edition).

### 10.1. Structure & Placement
- Position directly after the Web IDL block (`<pre class="idl">`) and before implementation algorithms. Do not mark it with `w-nodev`.
- **Signatures (`<dt>`)**: Describe JS usage. Use `<var>` for placeholder names. Register first introductions with `<span subdfn data-x="dom-IDL-name">`.
- **Explanation (`<dd>`)**: Explain behavior concisely using present-tense verbs ("Returns...", "Updates...", "Throws..."). Never use normative RFC2119 keywords ("must").

### 10.2. Exception Parity & Synchronization
- Document every `DOMException` that an API can throw explicitly in the `domintro` `<dd>` block (e.g., `Throws a "NotSupportedError" DOMException if...`).
- **Synchronization Rule**:
  - If normative algorithm steps change so that an exception is no longer thrown (e.g., falling through or returning null), **any domintro sentence promising that exception becomes false and must be removed**.
  - If normative steps add a new throwing condition, the domintro must document it.

### 10.3. Stale Warning Boxes
- Check existing `<p class="warning">` and `<p class="note">` blocks in the modified section.
- If a warning claims a method "performs no sanitization", and the PR introduces default policy or parser sanitization capabilities, the warning must be updated or qualified to prevent outdated information from misleading developers.

### 10.4. Qualified Interface Names in Method Intros
- When defining method steps for attributes or methods implemented across multiple interfaces (e.g. `innerHTML` on `Element` and `ShadowRoot`), qualify the intro explicitly:
  - *Correct*: `"The Element innerHTML setter steps are:"`
  - *Incorrect*: `"The innerHTML setter steps are:"` (ambiguous with ShadowRoot).

---

## 11. Developer's Edition (w-dev / w-nodev)

The HTML specification compiles into a **Living Standard** and a **Developer's Edition**.

- **What to Keep**: High-level overviews, descriptive introductions, authoring guidelines, examples (`<div class="example">`), and `<dl class="domintro">` blocks.
- **What to Omit**: Web IDL algorithmic rules, parser state machines, and implementer-only tree manipulations.
- **Attributes**:
  - Use `w-nodev` to exclude implementer-only content from Developer's Edition.
  - Do not nest `w-dev` or `w-nodev` attributes inside an ancestor already marked `w-nodev`.
  - Use `subdfn` on `<span data-x="...">` when defining terms whose primary `<dfn>` is omitted with `w-nodev`.

---

## 12. Working with Legacy Clauses & Refactoring

- **Consistency vs. Modern Style**:
  - *New Features / Rewrites*: Strictly follow modern guidelines.
  - *Minor Edits*: Prioritize local consistency. If modern rules make the patch look out-of-place within a legacy block, match the surrounding style.
- **Separation of Commits**:
  - Never mix structural/editorial cleanup (whitespace, IDL formatting, tag modernization) with functional/behavioral changes in the same commit.
  - Keep editorial cleanups in dedicated commits prefixed `Editorial: ...`.

---

## 13. Reviewing PR Descriptions & Cross-Spec Companion PRs

A rigorous review does not stop at the specification diff; the PR description and any linked companion PRs in external specifications are frequent vectors for architectural oversights, description drift, and out-of-sync contracts.

### 13.1. PR Description Hygiene & Preventing Drift
- **Description Drift / Staleness**: During multi-round reviews or stacked PR refactors, PRs frequently evolve. The PR description easily becomes stale, describing abandoned algorithms, dropped helpers, or obsolete parameters.
  - *Audit Rule*: The PR description MUST accurately represent the *final proposed diff*, not the author's initial draft.
  - *Pruning*: Explicitly remove references to dropped helpers (e.g., if a helper like "fold set and filter HTML" was eliminated during refactoring, update the PR description).
  - *Checklist Completeness*: Ensure the WHATWG PR template checklist is fully filled out (tests linked, engine bugs referenced, related issues tagged). Avoid empty test items or broken markdown links.
- **Documenting Intentional Scope Limits & Invariants**:
  - If sibling methods or edge-case legacy sinks are intentionally omitted from a refactor (e.g., `document.execCommand("insertHTML")` or XML document handling), the PR description should explicitly state that they are out-of-scope and explain the rationale.
  - Call out observable behavioral changes (such as text node coalescing differences, changes to mutation observer records, or custom element reaction timing).

### 13.2. Multi-Spec & Companion PR Review
Features touching parsing, security, loading, or scripting often span multiple specifications (e.g., HTML, DOM, Trusted Types, CSP, Fetch, Streams, URL, Web IDL). When a PR depends on or modifies an external spec:
- **Lockstep Companion Audit**:
  - Never review an HTML PR in isolation if it relies on an open companion PR in another repository (e.g., W3C Trusted Types or WHATWG DOM).
  - The reviewer MUST read the companion PR's diff and ensure the cross-spec contract matches in both directions.
- **Contract & Polarity Synchronization**:
  - Verify parameter order, types, and Boolean polarities across the spec boundary.
  - *Real-world failure mode (PR #12583 / TT #606)*: HTML expected streaming sinks to require `createParserOptions` and non-stream sinks to fall back, but the companion TT PR implemented `throwIfMissing` with reversed polarity!
- **Sentinel Objects vs. String Literals**:
  - When passing sentinel values defined in external specs (e.g., Trusted Types `Stream` sentinel), verify that the HTML algorithm passes the actual sentinel object rather than a string literal (e.g., `"Stream"`), which would trigger string conversions.
- **Anchor Fragment & Definition Matching**:
  - Ensure external `<dfn>` links and `data-x-href` attributes match the companion PR's anchor IDs exactly (including casing and hyphenation, e.g., `#trustedparseroptions-sanitizer-config`), preventing link rot or Wattsi build warnings.
- **Landing Order & Release Sequencing**:
  - Explicitly document the landing dependency sequence in both PR descriptions. If HTML depends on terms defined in an external spec, confirm whether the dependency PR must be merged first.

### 13.3. The "Editorial:" Prefix Trap on Observable Behavior
- **Never prefix a PR title or commit message with `Editorial:` if the change introduces ANY web-observable behavioral difference.**
  - *Failure Mode (from PR #12890 review)*: Tagging a commit as `Editorial:` when the algorithm change causes navigation timing entries to be created for `srcdoc`, `javascript:`, or error pages, or when it binds previously unbound parameters.
  - *Maintainer Impact*: WHATWG maintainers and automated bots rely on the `Editorial:` prefix as a signal to skip cross-browser implementer consensus checks, MDN documentation issues, and WPT tests.
  - *Rule*: If an algorithm alteration fixes an un-bound variable, changes a returned value, alters exception throwing, or modifies when an entry or event is queued, it is **normative**. Keep the commit message un-prefixed (or prefixed with the topic area, e.g. `Navigation timing: ...`).

---

## 14. Reviewing Web Platform Tests (WPT) & Coverage Auditing

A specification review is never complete without inspecting the accompanying Web Platform Tests (WPT). Reviewing the WPT PR diff in parallel with the spec diff is essential to catch edge cases, omitted sibling methods, and underspecified behaviors.

### 14.1. The Diff-to-Test Mapping (Audit Every Changed Branch)
- **Line-by-Branch Verification**: Every algorithmic condition (`If ...`, `Otherwise, if ...`, `Switch ...`, `Assert`, `throw a ... DOMException`) introduced or modified in the spec diff must have a corresponding test case in WPT.
- **Audit Sibling Call Sites**: Authors often write tests only for the flagship API that prompted the PR (e.g. `setHTML()`), while omitting tests for the 5 legacy methods (`innerHTML`, `outerHTML`, `insertAdjacentHTML`, `createContextualFragment`, `DOMParser`) that were refactored in the same spec diff.
  - *Review Rule*: Check that every modified caller in the spec PR is explicitly tested in WPT.

### 14.2. Negative Testing & Atomic Rollback
- Do not accept test suites that only test the "happy path".
- **Exact Exception Names**: Verify tests assert the exact `DOMException` name specified (`SyntaxError`, `NotSupportedError`, `HierarchyRequestError`, `TypeError`).
- **Atomicity Tests**: When an API is specified to validate options before mutating the DOM, the WPT must verify that throwing an exception leaves the destination DOM **completely untouched** (e.g., child nodes were not cleared or removed prior to throwing).
- **Disconnected Nodes**: Verify behavior when invoked on detached elements or nodes without parents (does it throw, no-op, or return a closed/errored stream?).

### 14.3. Combinatorial Matrix Coverage
- When an API introduces multiple configuration flags or modes (e.g. `safe` vs. `unsafe`, `runScripts: true` vs. `false` vs. omitted/default, synchronous vs. streaming), the WPTs must test the **Cartesian product** of those options.
- Test both the explicit values (`{ runScripts: false }`, `{ runScripts: true }`) and the default/omitted dictionary behavior (`{}`).

### 14.4. Context-Sensitive Node Edge Cases
Fragment parsing and DOM mutations vary significantly across node types. Ensure WPT coverage exists for:
- **`<template>` Elements**: Verify operations target `template.content` (`template contents`) rather than direct template children across all method variants.
- **Foster Parenting & Table Contexts**: Parsing fragments in `<table>`, `<tbody>`, `<tr>`, `<td>` contexts.
- **Form Contexts**: Parsing fragments inside `<select>` or `<optgroup>`.
- **Script Elements**: Parsing inside `<script>` in HTML and SVG namespaces (verifying script execution suppression or early null returns).
- **XML / XHTML Documents**: Verifying XML parsing vs. HTML parsing, and testing that XML-specific error conditions or unsupported modes throw as specified.

### 14.5. Testing Observable Side Effects & Invariants
- **Script Execution Suppression**: Assert that scripts do not execute under safe or `runScripts: false` modes (testing `<script>` tags, inline event handlers like `<img onerror=...>`, and SVG scripts).
- **Custom Elements & Shadow Roots**: Assert whether custom element constructors, `connectedCallback`, and declarative shadow roots fire, and test the exact timing of their reactions.
- **Text Node Coalescing**: If an algorithm alters parsing or insertion pipelines, test text node boundary merging via `childNodes.length`.

### 14.6. WPT Antipatterns to Catch
- **Engine-Driven vs. Spec-Driven Assertions**: Authors occasionally write WPT tests that assert current browser engine behavior (e.g. Chromium's current implementation) rather than what the specification change dictates. Reject tests that encode known engine bugs as expected behavior.
- **Tentative vs. Non-Tentative Files**:
  - Novel APIs not yet fully integrated into a ratified standard belong in `*.tentative.html` files.
  - Tests for bug fixes or normative changes to **pre-existing standard APIs** (e.g., `innerHTML` on `<template>` or XML throwing behavior) MUST be added to standard, non-tentative WPT files.

---

## 15. Automated Static Analyzers

The skill includes three deterministic Python static analyzers in `scripts/` to catch syntactic, IDL, variable lifecycle, and coverage failures automatically before or during spec review:

### 15.1. Web IDL Analyzer (`check_webidl.py`)
Validates `<pre class="idl">` blocks against WHATWG Web IDL guidelines:
- **Rule 1 (IDL-XREF-SPAN)**: Flags any `<code>` tags used inside `<pre class="idl">` (xrefs must use `<span>`).
- **Rule 2 (IDL-OPTIONAL-DICT-DEFAULT)**: Flags optional dictionary arguments that omit the required `= {}` default value.
- **IDL-NO-VAR**: Flags `<var>` tags used inside Web IDL declarations.
- **IDL-SINGLE-MEMBER-PER-LINE**: Flags multiple semicolon-terminated member declarations on a single line.

```bash
python3 scripts/check_webidl.py path/to/source.html
```

### 15.2. Algorithm Prose & Lifecycle Analyzer (`check_algorithms.py`)
Validates algorithm steps inside `<div algorithm>` blocks and spec markup:
- **Rule 4 (ALGO-UNDECLARED-SET / ALGO-DUPLICATE-LET)**: Validates variable lifecycle. Flags `Set <var>x</var> to` when `<var>x</var>` was never introduced with `Let`, and flags duplicate `Let <var>x</var> be` declarations in the same algorithm.
- **Rule 5 (ALGO-DEAD-INIT)**: Flags dead initializations where `Let <var>x</var> be null` is immediately followed by an `If/Otherwise` construct that overwrites `<var>x</var>` in every branch.
- **ALGO-UNBOUND-VAR-OUTER-SCOPE**: Flags variables declared with `Let` inside conditional sub-steps (`<ol>` depth >= 2) that are subsequently referenced at outer scope without an outer declaration.
- **ALGO-UNUSED-VAR**: Flags variables declared with `Let` that are never read/referenced again in the algorithm and omit `<var ignore>`.
- **ALGO-LIST-OF**: Flags `For each <var>x</var> in ...` (Infra list iteration requires `of`, not `in`).
- **ALGO-ASSERT-SPAN**: Flags bare `Assert:` lacking `<span>Assert</span>:` markup.
- **ALGO-REDUNDANT-DATA-X**: Flags redundant `data-x="term"` on `<span data-x="term">term</span>` where the cross-reference matches the definition name.
- **ALGO-NESTED-LIST-P**: Flags algorithm list items (`<li><p>...<ol>`) missing `</p>` before a nested `<ol>` or `<ul>`.
- **ALGO-STEP-PUNCTUATION**: Flags leaf algorithm steps missing terminal punctuation (`.` or `:`).
- **ALGO-NO-NEWLINE-BEFORE-GT**: Flags newlines immediately preceding `>` in HTML tags (`\n>`).
- **ALGO-DICT-TYPE-CHECK**: Flags invalid dictionary type checking (`If <var>options</var> is a <code>SomeOptions</code>:` or `is a dictionary`).
- **NAMESPACE-CASING**: Flags uppercase `<span>HTML Namespace</span>` or `<span>MathML Namespace</span>`.
- **ALGO-QUALIFIED-INTRO**: Flags unqualified method step intros (`"The innerHTML setter steps are:"`) when the method exists on multiple interfaces (`Element` vs `ShadowRoot`).

```bash
python3 scripts/check_algorithms.py path/to/source.html
```

### 15.3. WPT Coverage & Diff Analyzer (`check_wpt_coverage.py`)
Audits spec changes against accompanying Web Platform Tests:
- **WPT-MISSING-SINK-COVERAGE**: Extracts all modified IDL methods and algorithm sinks from the spec diff, scans the WPT directory/diff, and flags any modified sinks with zero test coverage (catching forgotten sibling methods like `ShadowRoot.innerHTML` or `createContextualFragment`).
- **WPT-MISSING-EXCEPTION-TEST**: Verifies that every `throw a "..." DOMException` in the spec algorithm has a corresponding `assert_throws_dom("...")` test.
- **WPT-TENTATIVE-ON-STANDARD-API**: Flags tests for pre-existing standard APIs erroneously placed in `.tentative.html` files.

```bash
python3 scripts/check_wpt_coverage.py --spec-file path/to/spec.html --wpt-dir path/to/wpt/
```

---

## 16. Comprehensive Self-Review & PR Review Checklist

Before finalizing or approving any HTML specification PR, run through this comprehensive checklist:

### Automated Static Analysis
- [ ] Run `python3 scripts/check_webidl.py <files>` (zero Web IDL xref or optional dict default errors).
- [ ] Run `python3 scripts/check_algorithms.py <files>` (zero variable lifecycle, scope leak, unused var, punctuation, or assertion errors).
- [ ] Run `python3 scripts/check_wpt_coverage.py --spec-file <spec> --wpt-dir <wpt>` (all modified sinks and exceptions covered).

### PR Description, Commit Hygiene & Companion PR Audit
- [ ] **No "Editorial:" Prefix on Observable Behavior**: Is the PR or commit prefixed with `Editorial:`? If the change causes entries to be created/queued, changes return values, or rejects promises, remove `Editorial:`.
- [ ] **PR Description Freshness**: Does the PR description match the actual final diff? Have mentions of dropped helpers, obsolete steps, or old syntax been pruned?
- [ ] **Checklist & Template Completeness**: Are WPT test links, issue links, and engine bugs properly documented without broken markdown links?
- [ ] **Scope Exclusions Noted**: Are intentional out-of-scope sibling sinks (e.g. legacy `execCommand`, XML document limits) documented in the PR body?
- [ ] **Companion PR Synchronization**: If a companion PR in another spec exists (e.g. Trusted Types, DOM, Fetch), has it been audited? Do parameter contracts, sentinel types, and boolean polarities agree in both directions?
- [ ] **Anchor & Link Validation**: Do cross-spec `data-x-href` links match the companion spec's exact exported anchor fragments?
- [ ] **Landing Order Established**: Is the merge sequence clearly stated between the companion PRs?

### Web Platform Tests (WPT) Coverage Audit
- [ ] **Diff-to-Test Mapping**: Does every new branch, throwing condition, and fallback path in the spec diff have an explicit test case?
- [ ] **Sibling Sinks Tested**: Are all modified parallel methods (`Element.innerHTML`, `ShadowRoot.innerHTML`, `outerHTML`, `insertAdjacentHTML`, `createContextualFragment`, `setHTML`) tested, not just the primary new API?
- [ ] **Atomicity Tested**: Are tests present verifying that when an exception is thrown, the destination DOM remains pristine and unmutated?
- [ ] **Context-Sensitive Elements**: Are tests included for `<template>`, `<table>`/`<tbody>`, `<select>`, `<script>`, and XML/XHTML documents?
- [ ] **Fallback Paths Tested**: Are tests present for non-fetch / null-controller navigations (`about:srcdoc`, `javascript:`, error pages)?
- [ ] **Combinatorial Matrix**: Are all combinations of boolean flags (e.g. `safe` × `runScripts` false/true/default) tested?
- [ ] **Spec vs. Engine Truth**: Do tests assert the normative spec behavior rather than current browser engine quirks?
- [ ] **Tentative Naming Correctness**: Are fixes to existing standard methods placed in non-tentative files, while novel APIs use `.tentative.html`?

### Algorithmic Correctness & State
- [ ] **Scope Leaks & Unbound Variables**: Are any variables declared with `Let` inside conditional sub-lists (`<ol>`) referenced outside that branch? (Initialize with `Let <var>x</var> be null` in outer scope).
- [ ] **Pre-Initialization State Access**: Are capability checks, permissions policy, or environment settings queried on an object *before* its subordinate objects (`window.document`, parent) are linked?
- [ ] **Fallback & Null Path Auditing**: When guarding an algorithm step with `If <var>controller</var> is non-null:`, what happens on the fallback path (`srcdoc`, `javascript:`, error pages)? Are entries or state dropped?
- [ ] **Shallow Clones**: Are any cloned dictionaries/maps holding nested maps/lists? If so, are mutations safely isolated, or do they leak into the source object?
- [ ] **Temporal State Snapshots**: Are dynamic locations (`adjusted insertion location`, context node, open elements) captured *before* any insertion or tree mutation?
- [ ] **Object Construction Ordering**: Are all flags/modes finalized before object construction, or are object internal slots explicitly updated afterward?
- [ ] **Atomic Failure**: Are option validation, parser creation, and type checks performed *before* any destructive DOM mutations (clearing children, detaching nodes)?
- [ ] **Dictionary Types in Algorithms**: Are there any invalid `If options is a FooOptions` checks? (Check keys via `exists` or default fallback instead).

### Parser & Tree Construction
- [ ] **Adoption Agency Algorithm**: Does AAA create, reparent, or clone elements without your new checks? Are parentless `lastNode` and self-append loops prevented?
- [ ] **Root & Body Attribute Merging**: Do duplicate start tags merge attributes without passing through element sanitization/validation?
- [ ] **Speculative Parsing**: Does speculative parsing reflect any new blocking, sanitization, or script rules?
- [ ] **Template Redirection**: Does every insertion method redirect `HTMLTemplateElement` to `template.content`?

### Call Site & Architecture Audit
- [ ] **Exhaustive Call Sites**: Have all sibling entry points (`Element.innerHTML`, `ShadowRoot.innerHTML`, `outerHTML`, `insertAdjacentHTML`, `createContextualFragment`, `parseFromString`, `setHTML`, `parseHTML`) been audited for signature changes?
- [ ] **No Masking Defaults**: Are internal abstract algorithm parameters mandatory where defaults could silently mask forgotten callers?
- [ ] **Real Sink Names**: Are sink names passed to security violation reporting actual API names (e.g. `"Element innerHTML"`), never synthetic names (`"Sanitizer"`)?
- [ ] **Cross-Spec Sentinels**: Are sentinels passed as proper specification objects, not string literals?

### Web IDL, Prose & Markup
- [ ] **IDL Cross-References**: Do cross-references inside `<pre class="idl">` use `<span>` exclusively, without `<code>`?
- [ ] **Optional IDL Dictionaries**: Do optional dictionaries without required members specify `= {}`?
- [ ] **Variable Declarations**: Does the first assignment use `Let` and subsequent assignments use `Set`? No duplicate declarations or dead initializations?
- [ ] **Unused Variables**: Are all `Let`-bound variables referenced in subsequent steps (or marked `<var ignore>`)?
- [ ] **List Iteration Keyword**: Does iteration use `For each <var>x</var> of <var>list</var>` (never `in`)?
- [ ] **Assertion Markup**: Are assertions formatted as `<span>Assert</span>:`?
- [ ] **Redundant data-x**: Are redundant `data-x` attributes removed when matching concept text?
- [ ] **Nested List Closures**: Are `<p>` tags closed before nested `<ol>` or `<ul>` lists?
- [ ] **Step Punctuation**: Do algorithm steps end with a period `.` or colon `:`?
- [ ] **Line Wrapping & Tags**: Are lines wrapped at 100 characters? No newlines immediately before `>`?
- [ ] **Grammatical Conjunctions**: Did removing an item from a list preserve the "and"/"or" conjunction?

### Domintro & Documentation
- [ ] **Exception Parity**: Do domintro `<dd>` exception statements match the actual normative throwing behavior?
- [ ] **Stale Warnings**: Have `<p class="warning">` and notes been updated to reflect new policy, parser, or security capabilities?
- [ ] **Interface Qualification**: Are multi-interface methods qualified (e.g. `"The Element innerHTML setter steps are:"`)?


