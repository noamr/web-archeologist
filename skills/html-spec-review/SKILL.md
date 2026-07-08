---
name: html-spec-review
description: Guidelines for writing and reviewing the HTML standard. Used to enforce style, formatting, prose correctness, and developer's edition annotations.
---

# Agent Skill: HTML Specification Writing and Review Guide

This skill provides the official guidelines, prose style conventions, and formatting constraints for writing, editing, and reviewing the WHATWG HTML standard. Refer to this skill when generating new spec text, reviewing pull requests, or updating existing sections of the HTML specification.

---

## 1. Developer's Edition (w-dev / w-nodev)
The HTML specification compiles into a **Living Standard** and a **Developer's Edition** (which filters out low-level implementer-only details).

### A. What to Keep vs. Omit
*   **Keep in Developer's Edition**:
    *   High-level overviews, descriptive introductions, and authoring guidelines.
    *   Examples (`<div class="example">...</div>`).
    *   `<dl class="domintro">` blocks describing Web IDL interfaces.
    *   Notes explaining common authoring scenarios.
*   **Omit from Developer's Edition**:
    *   Web IDL definition blocks (`<pre class="idl">`) - *Automatically omitted by the build; no manual attribute needed.*
    *   Algorithmic steps defining IDL attribute getters, setters, and method behaviors.
    *   Low-level concepts, parsing rules, and instructions for browser engine implementers.

### B. Markup Annotations
*   **`w-nodev`**: Use this attribute to exclude block or inline elements from the Developer's Edition.
    ```html
    <div w-nodev>
      <p>This paragraph is only of interest to user agent implementers.</p>
    </div>
    ```
*   **`w-dev`**: Use this attribute to include elements *only* in the Developer's Edition.
*   **`subdfn`**: When a term is defined in a section omitted from the Developer's Edition (like a Web IDL block), add `subdfn` on a matching `data-x` element to specify its definition for the Developer's Edition.

### C. Nesting Constraints
*   **No Redundant Nesting**: Do not nest `w-dev` or `w-nodev` attributes inside an ancestor element that is already marked `w-nodev`.
*   **Minimize Scope**: Avoid wrapping minor sentence fragments, words, or individual punctuation marks with `w-nodev` if it clutters the HTML source.

---

## 2. Formatting and Markup Rules

### A. Line Length and Wrapping
*   **Wrap limit**: Strictly wrap lines at **100 characters**.
*   **Whitespace & Inline Elements**: Do not insert newlines between inline tag names and their text content if it introduces unwanted spaces.
    *   *Incorrect*:
        ```html
        Set its <i data-x="force-quirks flag">
        force-quirks flag</i> to...
        ```
    *   *Correct*:
        ```html
        Set its <i data-x="force-quirks flag">force-quirks flag</i> to...
        ```
*   Attributes and whitespace inside attribute values can contain newlines to respect the 100-character line wrap.

### B. Element Hierarchy & Indentation
*   **`<li>` Elements**: Every list item (`<li>`) must wrap its text content in a `<p>` element, unless it is a direct child of `<ul class="brief">`.
*   **List Item Spacing**: List items (`<li>`, `<dt>`, `<dd>`) must start on a new line, with a blank line separating consecutive items. Do not add blank lines at the absolute start or end of the list.
    ```html
    <ol>
     <li><p>Step one.</p></li>

     <li><p>Step two.</p></li>
    </ol>
    ```
*   **Block-in-Block same-line nesting**: If a block element contains a single block child (e.g. `<li><p>...`), do not split them onto new lines.
*   **Indentation**: Only indent for a new child block element.
*   **Preformatted Code Blocks**: Do not bundle multiple sibling `<code>` blocks inside a single `<pre>`. Use separate `<pre><code class="...">` blocks.
*   **Quotes & End Tags**: End tags must not be omitted (unless consistent with the surrounding legacy file block). Attribute values must use double quotes.

### C. Web IDL Blocks Formatting
*   **Web IDL Parameters**: Inside Web IDL blocks (e.g. `<pre class="idl">` or `<code class="idl">`), parameter names and type names must **not** be wrapped in `<var>` tags.
    *   *Incorrect*: `undefined queueMicrotask(VoidFunction <var>callback</var>);`
    *   *Correct*: `undefined queueMicrotask(VoidFunction callback);`

### D. Lists and Tables: Brief, Switch, and tabular layout
*   **Brief Lists (`<ul class="brief">`)**:
    *   Use for simple, short items (e.g., terms, variable names, list of options, or short conditions).
    *   **Markup constraint**: Items in a `brief` list must **not** wrap their content in a `<p>` tag (e.g. use `<li>term</li>` rather than `<li><p>term</p></li>`).
    *   Do **not** leave blank lines between items in a `brief` list.
*   **Switch Lists (`<dl class="switch">`)**:
    *   Use inside algorithms or steps for conditional branching / case logic.
    *   Each condition is specified inside one or more `<dt>` tags (e.g., `<dt>If it is a quotation mark</dt>`, `<dt>Otherwise</dt>`).
    *   The consequence/action is specified in the subsequent `<dd>` tag.
    *   **Fall-through case**: Multiple sibling `<dt>` tags can be grouped together to share the same `<dd>` tag.
*   **When to Use Lists vs. Tables**:
    *   **Use Lists** (`brief` `<ul>`, `<ol>`, or `switch` `<dl>`): For sequential steps, simple branches, or flat lists of terms.
    *   **Use Tables (`<table>`)**: Only when presenting tabular mappings of multiple dimensions (e.g., mapping event names to event handler attributes and event interfaces, or listing element tags and their properties). Do not use tables for simple branch logic or sequential steps.

---

## 3. Algorithms & Variable Scoping

### A. Algorithm Container
*   Every algorithm must be wrapped in a `<div algorithm> ... </div>` block.
*   Do not indent the contents of the `<div algorithm>`.
*   Do not assign a value to the `algorithm` attribute (i.e. use `<div algorithm>`, NOT `<div algorithm="name">`).
*   Include the algorithm's preamble (e.g. name, parameters, return type) inside the `<div algorithm>` container.

### B. Variable Scoping (`<var>` and `var-scope`)
*   Every `<var>` element must be scoped. It is considered scoped if it is:
    1.  Inside a `<div algorithm>` container.
    2.  Inside an element with the `var-scope` attribute.
    3.  Inside a `<dl class="domintro">` block.
    4.  Marked with the `ignore` attribute.
*   **Multi-Algorithm Scope**: If multiple consecutive algorithms share variables, wrap them in `<div var-scope> ... </div>`.
*   **Single-use Warning**: If a variable name appears only once inside an algorithm, the build compiler will raise a warning. If this is intentional, add the `ignore` attribute: `<var ignore>x</var>`.

### C. Markup for Assertions, Context, and Arguments
*   **Assertions**: Always wrap the word "Assert" in a `<span>` element.
    ```html
    <li><p><span>Assert</span>: <var>x</var> is not null.</p></li>
    ```
*   **`this` Context**: Wrap the keyword `this` in a `<span>` rather than a `<var>` when referencing the current instance in getter/setter steps.
    ```html
    <li><p>If <span>this</span> has a custom value, return it.</p></li>
    ```
*   **External Arguments/Parameters**: When invoking or passing arguments to external algorithms or ECMAScript abstract operations, mark the arguments using italic tags (`<i>name</i>`) instead of `<var>name</var>`.
    ```html
    <li><p>Run the <span>focusing steps</span> for <var>target</var>, with the <code>Document</code>'s <span>viewport</span> as the <i>fallback target</i>.</p></li>
    ```

### D. Getter and Setter Steps Style
*   Rather than wrapping getter/setter behavioral descriptions in a `<dl>` with `<dt>/<dd>` saying "Must return...", use a flat paragraph format starting with:
    `The <dfn attribute for="...">attribute</dfn> getter/setter steps are to [do something].`
    *   *Example*: `The <dfn attribute for="NavigatorID"><code data-x="dom-navigator-userAgent">userAgent</code></dfn> getter steps are to return the default User-Agent value.`

---

## 4. Prose Style and Grammar

### A. Conditional Statements
*   Always use the full **"If [condition], then [consequence]"** structure. Do not omit "then".
    *   *Incorrect*: "If <var>x</var> is true, return."
    *   *Correct*: "If <var>x</var> is true, **then** return."
*   **Nesting Conditions**: When nesting 3 or more conditions, format them as a brief bulleted list:
    ```html
    <li>
     <p>If all of the following are true:</p>

     <ul class="brief">
      <li><p>condition 1;</p></li>

      <li><p>condition 2; and</p></li>

      <li><p>condition 3,</p></li>
     </ul>

     <p>then...</p>
    </li>
    ```

### B. "otherwise" and "if-then-otherwise" Formatting
*   **The "then" omission rule**: Once the keyword "otherwise" is used, the keyword "then" is omitted.
    *   *First branch*: `If [condition], then [consequence].`
    *   *Subsequent branches*: `Otherwise, if [condition], [consequence].` (Note the comma after "Otherwise", the comma after the condition, and the lack of "then").
        *   *Incorrect*: "Otherwise, if <var>x</var> is true, **then** set <var>y</var> to 1."
        *   *Correct*: "Otherwise, if <var>x</var> is true, set <var>y</var> to 1."
    *   *Fallback branch*: `Otherwise, [consequence].`
        *   *Correct*: "Otherwise, throw a <code>TypeError</code>."
*   **Ternary and Semicolon usage ("; otherwise")**: For inline or single-sentence variable assignments/returns of the form `[value1] if [condition]; otherwise [value2]`:
    *   Place a **semicolon** before `otherwise`.
    *   Do **not** place a comma after `otherwise` if it is followed by a short value expression (like `null`, `failure`, or a variable name).
        *   *Correct*: `Let <var>baseURL</var> be <var>environment</var>'s base URL, if <var>environment</var> is a <code>Document</code> object; otherwise <var>environment</var>'s API base URL.`
        *   *Correct*: `Returns true if the form's controls are all valid; otherwise, returns false.` (Use comma after otherwise if followed by a verb phrase).


### B. Navigation & Exit prose
*   **Return**: Use "return" or "return <var>value</var>" to exit a whole algorithm or method.
*   **Abort**: Use "abort these steps" when terminating a set of sub-steps or an asynchronous "in parallel" sequence, allowing the outer/calling procedure to continue.

### C. Terminology and Formatting Conventions
*   **Omit "the string" Prefix**: Avoid prefixing string literals with "the string".
    *   *Incorrect*: "...match for the string `<code data-x="">text/html</code>`"
    *   *Correct*: "...match for `<code data-x="">text/html</code>`"
*   **Active/Inline Conjugation**: Conjugate algorithms naturally in English prose rather than stating them procedurally.
    *   *Incorrect*: "the result of running <span>get the popcorn</span>"
    *   *Correct*: "the result of <span data-x="get the popcorn">getting the popcorn</span>"
*   **Grammar & Spelling**:
    *   Use American English spelling (e.g. `behavior`, `color`, `serialized`).
    *   Ensure correct indefinite articles (e.g. "**an** inline-size" instead of "a inline-size").
    *   Always use Oxford commas in parameter/argument listings.

### D. Casing of Enum and State Values in Prose
*   When referencing defined enum, state, or mode values in spec prose, make sure to capitalize them exactly as defined in their `<dfn>`.
    *   *Incorrect*: "...if <span>scripting mode</span> is disabled"
    *   *Correct*: "...if <span>scripting mode</span> is <span>Disabled</span>"

---

## 5. Infra Data Structures and Iteration

### A. List Operations and Syntax
*   **Literal List Syntax**: Wrap inline lists in double angle brackets (`« »`).
    *   *Example*: `Let <var>list</var> be « "a", "b", "c" ».`
*   **Index and Size**: Use zero-based square bracket index (e.g. `list[0]`) and the term `size` (not `length` or `count`).
    *   *Example*: `If <var>list</var>'s size is not 3, then return.`
*   **Multiple Assignment**: Assign list items using the `« »` destructuring syntax.
    *   *Example*: `Let « <var>a</var>, <var>b</var>, <var>c</var> » be <var>list</var>.`
*   **Standard Verbs**:
    *   `append` (to add to the end).
    *   `extend A with B` (to append all items of list B to list A).
    *   `prepend` (to add to the start).
    *   `replace ... within ...` (to update matching items).
    *   `insert ... into ... before [index]`.
    *   `remove ... from ...`.
    *   `contains` / `does not contain` (for inclusion checks).
    *   `is empty` / `is not empty`.

### B. Map Operations and Syntax
*   **Literal Map Syntax**: Wrap inline maps in double angle brackets and square brackets (`«[ key → value ]»`). Note the right arrow `→`.
    *   *Example*: `Let <var>map</var> be «[ "a" → 1, "b" → 2 ]».`
*   **Lookup with Defaults**: Use the indexing syntax, optionally adding the `with default` clause.
    *   *Example*: `Let <var>val</var> be <var>map</var>["a"] with default 0.`
*   **Key Existence**: Check existence using `exists`.
    *   *Example*: `If <var>map</var>["key"] exists, then...`
*   **Standard Map Verbs**:
    *   `set map[key] to value`.
    *   `remove map[key]`.
    *   `clear map` (to empty the map).
    *   `get the keys` (returns an ordered set of keys).
    *   `get the values` (returns a list of values).
    *   `map's size` (size of the keys list).
    *   `is empty` / `is not empty`.

### C. Structs and Tuples
*   **Structs**: To define a struct with named properties, use the `whose ... is` construction:
    *   *Example*: `Let <var>email</var> be an email whose local part is "hostmaster" and host is infra.example.`
*   **Tuples**: To define an ordered struct, wrap literal values in parentheses:
    *   *Example*: `Let <var>statusInstance</var> be the status (200, "OK").`
    *   *Access*: Access fields by name (e.g. `statusInstance's code`) or by zero-based index (e.g. `statusInstance[0]`).

### D. Loop Iterations
*   **For Each Loop**: When iterating over lists/maps, use the keyword **"of"** instead of "in".
    *   *Correct*: `For each <var>node</var> of <var>nodes</var>:`
    *   *Incorrect*: `For each <var>node</var> in <var>nodes</var>:`
*   **Map Iteration**: Iterate maps by key-value pairs:
    *   *Example*: `For each <var>key</var> → <var>value</var> of <var>map</var>:`
*   **While Loops**: Use the format: `While [condition]:` followed by nested ordered steps.
*   **Flow Control**:
    *   `continue`: Skip the remaining steps of the current iteration, moving to the next item.
    *   `break`: Exit the loop entirely.

---

## 6. Writing domintro Blocks
A `<dl class="domintro">` block provides a non-normative, developer-friendly introduction to Web IDL interfaces, attributes, and methods. Because Web IDL blocks and normative algorithmic steps are omitted from the **Developer's Edition**, `domintro` blocks are the primary reference source for developers reading the spec.

### A. Structure and Placement
*   Wrap the block in `<dl class="domintro"> ... </dl>`.
*   Place it directly after the Web IDL block (`<pre class="idl">`) and before the normative implementation algorithms.
*   Do not mark the `domintro` block with `w-nodev` (it must remain visible in the Developer's Edition).

### B. Defining Member Signatures (`<dt>`)
*   Describe usage from a JavaScript perspective (not Web IDL syntax).
*   Use `<var>` tags for placeholder variable names (e.g. `<var>element</var>`, `<var>value</var>`, `<var>index</var>`).
*   **The `subdfn` link**: The first time an IDL attribute or method name is introduced in the block, wrap it in `<span subdfn data-x="dom-IDL-name">` to register it as the definition for the Developer's Edition.
*   Subsequent signatures in the same block for that member should use a normal `<span>` (e.g. `<span data-x="dom-IDL-name">`).
    ```html
    <dl class="domintro">
     <dt><code data-x=""><var>element</var>.<span subdfn data-x="dom-HTMLOrSVGElement-nonce">nonce</span></code></dt>
     <dd><p>Returns the nonce value...</p></dd>

     <dt><code data-x=""><var>element</var>.<span data-x="dom-HTMLOrSVGElement-nonce">nonce</span> = <var>value</var></code></dt>
     <dd><p>Updates the nonce value...</p></dd>
    </dl>
    ```

### C. Explaining Behavior (`<dd>`)
*   Summarize getters, setters, and methods clearly and concisely.
*   Use descriptive, present-tense verbs (e.g. "Returns...", "Updates...", "Throws...") rather than normative implementer phrasing (avoid "must").
*   Explicitly mention return values, side effects (e.g. "Checks the checkbox...", "Throws an "InvalidStateError" DOMException if..."), and default behaviors.
*   Keep definitions high-level and focused on author/developer utility.

---

## 7. Working with Legacy Clauses (Consistency vs. Modern Style)
The HTML specification is a large, long-lived document. Many older parts of the standard (such as the HTML parser section) were written before modern formatting rules, variable scoping validations, and style guidelines were established.

### A. The Golden Rule
*   **For New Features and Major Rewrites**: Always strictly follow the modern guidelines. Never copy legacy styles or anti-patterns.
*   **For Small Edits and Local Patches**: Prioritize local consistency when making minor corrections (e.g., fixing a single step or a typo in a legacy algorithm). If applying a modern rule locally makes the edited lines stand out or format inconsistently with surrounding steps, match the local surrounding style.

### B. Refactoring Legacy Code (Separation of Concerns)
*   **Separate Commits**: Do not mix structural style refactorings with user-facing functional changes in the same commit.
*   If a legacy section needs modernization, do it in a dedicated editorial commit or PR (e.g., labeled `Editorial: clean up markup of [Section]`).


