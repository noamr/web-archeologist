---
name: html-spec-review
description: Guidelines for writing and reviewing the HTML standard. Used to enforce style, formatting, prose correctness, and developer's edition annotations.
---

# Agent Skill: HTML Specification Writing and Review Guide

> **Note on Extended Guidelines:**
> For comprehensive guidance on substantive architectural judgment (including threading models, backwards compatibility, API design consistency, and state encapsulation) across W3C, WHATWG, and WICG specifications, as well as additional Bikeshed/Wattsi syntax rules, please refer to the external [spec-writing-skill repository](https://github.com/domfarolino/spec-writing-skill). You may want to instruct the user to install it for more advanced specification authoring capabilities.

This skill provides the official guidelines, prose style conventions, and formatting constraints for writing, editing, and reviewing the WHATWG HTML standard. Refer to this skill when generating new spec text, reviewing pull requests, or updating existing sections of the HTML specification.

---

## 1. Formatting and Markup Rules

*   **Line Wrapping**: Strictly wrap lines at **100 characters**.
    *   Attributes or their values can contain newlines to respect this.
    *   Do not insert newlines between inline tag names and text if it inserts unwanted spaces (e.g., `<i data-x="...">\ntext</i>` is incorrect).
*   **List Formatting (`<li>`, `<dt>`, `<dd>`)**:
    *   Every `<li>` must wrap its text content in a `<p>` (except in `<ul class="brief">`).
    *   Format as `<li><p>Text</p></li>` on the same line if possible, or indent nested blocks.
    *   Separate consecutive list items with a blank line. Do not put blank lines at the list's absolute start/end.
*   **List Item Indentation**: Inside `<ol>` or `<ul>` (except brief lists):
    *   `<li>` is indented by 3 spaces.
    *   Subsequent lines within the `<li>` (including nested `<p>` or `<p class="note">` tags, or subsequent wrapped lines of text) must be indented by **4 spaces**.
*   **Web IDL Blocks (`<pre class="idl">`)**:
    *   Every IDL member, attribute, and operation must be on its own separate line. Never place multiple declarations on the same line.
    *   Do not wrap parameter names or type names in `<var>` tags inside Web IDL blocks.
*   **Brief Lists (`<ul class="brief">`)**: Use for simple/short lists. Items must **not** wrap content in a `<p>` tag. No blank lines between items.
*   **Switch Lists (`<dl class="switch">`)**: Use for complex branch logic. Sibling `<dt>` conditions map to a single `<dd>` consequence/action.
*   **Tables (`<table>`)**: Use only for multi-dimensional data (e.g., event tables, element properties). Do not use for simple steps or branching.
*   **Attributes & Tags**: Always use double quotes for attributes. Never omit end tags (always close all `<p>` and `<li>` tags).

---

## 2. Algorithms & Variable Scoping

*   **Algorithm Container**: Wrap every algorithm in a `<div algorithm>` (no assigned value). Include the preamble (name, return type) inside it. Do not indent the container's contents.
*   **Variable Scoping**: Wrap `<var>` elements to scope them. Multi-algorithm scopes can use `<div var-scope>`. If a variable is only used once, add the `ignore` attribute: `<var ignore>x</var>`.
*   **Variables Initialization**: Use the "initially" pattern when declaring variables or state, e.g., "...initially null", "...initially false", or "...initially the empty list « »".
*   **Variable Mutation vs. Declaration**: Use **"Set `<var>x</var>` to `<var>y</var>`"** when modifying or reassigning an existing variable, property, or flag. Reserve **"Let `<var>x</var>` be `<var>y</var>`"** strictly for initial variable declarations.
    *   *Correct*: `If <var>condition</var>, then set <var>mode</var> to "<code data-x="">same-origin</code>".`
*   **Callback & Sub-algorithm Signatures**: When defining steps to pass as callbacks to other specifications (e.g., Streams `abortAlgorithm`, `writeAlgorithm`, `pullAlgorithm`, `transformAlgorithm`, or Promise reactions), declare the expected parameters explicitly using `given <var>arg</var>:` matching the caller spec's invocation signature.
    *   *Example*: `Let <var>abortAlgorithm</var> be the following steps given <var>reason</var>:`
*   **Markup Styles**:
    *   *Assertions*: Wrap the word "Assert" in a `<span>` (e.g., `<span>Assert</span>:`).
    *   *Context*: Wrap `this` keyword in a `<span>` (e.g., `<span>this</span>`).
    *   *External Arguments*: Wrap external arguments in italics (`<i>arg</i>`), not `<var>`.
*   **Getter/Setter steps**: Use the flat format: "The <dfn attribute for="..."><code>attribute</code></dfn> getter/setter steps are to [do something]." or "The [...] getter steps are:" followed by a list.
*   **Keep it Terse & Clean**:
    *   *Conciseness*: Keep prose as short and direct as possible.
    *   *Inlining*: Inline unexported algorithms/operations if they are only invoked/called from a single place.
    *   *Cleanup*: Remove duplicate variables, unused variables, and redundant steps/checks (e.g. redundant null checks or early silent-return steps that bypass centralized validation algorithms).

---

## 3. Prose Style and Grammar

*   **Conditional Statements**:
    *   *Inline consequence*: Use the full **"If [condition], then [consequence]"** structure (e.g., "If <var>x</var> is true, **then** return.").
    *   *Block/Sub-list consequence*: Omit "**then**" and end with a colon (e.g., "If <var>x</var> is true:" followed by a nested list).
    *   *Multiple conditions (more than two)*: Use **"If any of the following are true:"** etc, followed by a `<ul>` containing the conditions, with the consequence in a subsequent `<p>` starting with "then...". Do not chain multiple "or" clauses in inline prose.
        ```html
        <li>
         <p>If any of the following are true:</p>

         <ul>
          <li><p><var>urlRecord</var> is failure;</p></li>

          <li><p><var>urlRecord</var>'s <span data-x="concept-url-scheme">scheme</span> is "<code
          data-x="">data</code>" or "<code data-x="">javascript</code>"; or</p></li>

          <li><p>running <span>Is base allowed for Document?</span> on <var>urlRecord</var> and
          <var>document</var> returns "<code data-x="">Blocked</code>",</p></li>
         </ul>

         <p>then set <var>element</var>'s <span>frozen base URL</span> to <var>document</var>'s
         <span>fallback base URL</span> and return.</p>
        </li>
        ```
*   **Branching & Fallbacks ("otherwise")**:
    *   *Subsequent branches*: "Otherwise, if [condition], [consequence]." (No "then" keyword).
    *   *Fallback branch*: Use a simple "**Otherwise, [consequence]**" or "**Otherwise:**". Do not repeat negative conditions from previous branches.
    *   *Inline Ternary*: Use the format: `[value1] if [condition]; otherwise [value2]` (note the semicolon before `otherwise`, and no comma after unless followed by a verb phrase).
*   **Antonym and Negative Concept Linking**:
    *   When setting boolean flags or checking disabled states, link to the explicit negative definition rather than linking the negative phrase to the positive definition.
    *   *Example*: `concept-n-script` defines "scripting is enabled", whereas `concept-n-noscript` defines "scripting is disabled". Use: `Set <var>parser</var>'s <span>parser scripting disabled</span> to true if <span data-x="concept-n-noscript">scripting is disabled</span> for <var>document</var>; otherwise false.`
*   **Enums, Actions, and State Values**:
    *   *Web IDL Enums*: Defined as `"butt"`. Reference in prose as `"<code data-x="">butt</code>"`.
    *   *Defined Enums / Actions*: Defined as `<dfn data-x="...">"no-referrer"</dfn>` or `<dfn data-x="...">"Remove"</dfn>`. Reference when returning or checking as `<span data-x="...">"no-referrer"</span>` or `<span data-x="...">"Remove"</span>`.
    *   *States & Modes*: Capitalize exactly as defined in their definition (e.g., `<span>Disabled</span>`).
*   **Standard Namespaces Casing**:
    *   All standard namespace cross-references use lowercase `"namespace"`:
        *   `<span>HTML namespace</span>`
        *   `<span>SVG namespace</span>`
        *   `<span>MathML namespace</span>` (not `<span>MathML Namespace</span>`)
        *   `<span>XML namespace</span>`
        *   `<span>XLink namespace</span>`
        *   `<span>XMLNS namespace</span>`
*   **Navigation & Exit**: Use "return" or "return <var>value</var>" for entire algorithms; "abort these steps" for sub-steps or parallel sequences.
*   **Conventions**:
    *   Omit "the string" prefix before string literals (e.g., "match for `<code data-x="">text/html</code>`").
    *   Conjugate active/inline algorithms (e.g. "result of <span data-x="...">getting the popcorn</span>" instead of "result of running get the popcorn").
    *   Use American English (`behavior`, `color`) and Oxford commas in listings.

---

## 4. Infra Data Structures and Iteration

*   **Lists**:
    *   Literal syntax: `Let <var>list</var> be « "a", "b" ».`
    *   Destructuring: `Let « <var>a</var>, <var>b</var> » be <var>list</var>.`
    *   Access & Size: Use zero-based index `list[0]` and `size` (never `length` or `count`).
    *   Verbs: `append`, `extend A with B`, `prepend`, `replace ... within ...`, `insert ... into ... before [index]`, `remove ... from ...`, `contains`, `is empty`.
*   **Maps**:
    *   Literal syntax: `Let <var>map</var> be «[ "a" → 1 ]».` (use right arrow `→`).
    *   Access & Default: `map["key"]` or `map["key"] with default 0`. Check existence with `exists`.
    *   Verbs: `set map[key] to value`, `remove map[key]`, `clear map`, `get the keys`, `get the values`, `map's size`.
*   **Structs & Tuples**:
    *   Struct: `Let <var>x</var> be a struct whose property is value.`
    *   Tuple: `Let <var>x</var> be (value1, value2).` Access by field name or index (`x[0]`).
*   **Loops**:
    *   For each: `For each <var>item</var> of <var>items</var>:` (use **of**, not in).
    *   Map entries: `For each <var>key</var> → <var>value</var> of <var>map</var>:`
    *   While: `While [condition]:`. Control with `continue` and `break`.

---

## 5. Writing domintro Blocks
`<dl class="domintro">` provides developer-friendly Web IDL explanations since IDL/normative steps are hidden in the Developer's Edition.

*   **Placement**: Position directly after the Web IDL block (`<pre class="idl">`) and before implementation algorithms. Do not mark it with `w-nodev`.
*   **Signatures (`<dt>`)**:
    *   Describe JS usage. Use `<var>` for placeholder names.
    *   Use `<span subdfn data-x="dom-IDL-name">` on the first introduction of a member to register it. Use normal `<span>` for subsequent signatures.
*   **Explanation (`<dd>`)**:
    *   Explain behavior concisely using present-tense verbs ("Returns...", "Updates...", "Throws..."). Avoid implementer terms (never use "must").
    *   Specify key return values, side effects, and thrown exceptions.
*   **Exception Parity & Synchronization**:
    *   Document every `DOMException` that an API can throw explicitly in the `domintro` `<dd>` block (e.g., `Throws a "NotSupportedError" DOMException if...`).
    *   Ensure normative algorithm steps actually throw the promised exception (rather than silently returning null or undefined), and maintain parity across synchronous and streaming variants of methods.

---

## 6. Working with Legacy Clauses

*   **Consistency vs. Modern Style**:
    *   *New Features / Rewrites*: Strictly follow modern guidelines.
    *   *Minor Edits*: Prioritize local consistency. If modern rules make the patch look out-of-place within a legacy block, match the surrounding style.
*   **Refactoring separation**: Never mix structural refactoring with functional changes in the same commit. Commit modernizations in separate commits (e.g., prefixed `Editorial: clean up markup of [Section]`).

---

## 7. Developer's Edition (w-dev / w-nodev)
The HTML specification compiles into a **Living Standard** and a **Developer's Edition** (which filters out low-level implementer-only details).

*   **What to Keep**: High-level overviews, descriptive introductions, authoring guidelines, examples (`<div class="example">`), and `<dl class="domintro">` blocks.
*   **What to Omit**: Web IDL block behaviors, parsing rules, and implementer-only steps.
*   **`w-nodev` / `w-dev`**: Use to exclude/include elements from/in the Developer's Edition.
    *   *No Redundant Nesting*: Do not nest `w-dev` or `w-nodev` attributes inside an ancestor already marked `w-nodev`.
    *   *Minimize Scope*: Avoid wrapping minor sentence fragments or individual punctuation if it clutters the HTML.
*   **`subdfn`**: If a term is defined inside an omitted Web IDL block, add `subdfn` on the corresponding `<span data-x="...">` definition so it stays defined in the Developer's Edition.
