# Typography Reference (Fancy Lists)

This document exercises the styles defined in the bundled pandoc reference template.
It uses **fancy lettered and roman list markers**, so it is meant to be converted to
`.docx`, not read as raw markdown.

## Heading Level 2

A normal body paragraph with **bold text**, *italic text*, and a bit of `inline code`
to test the default character styles. Here is a [hyperlink](https://example.com) for
the Hyperlink style.

### Heading Level 3

Some text that introduces the next level of detail.

#### Heading Level 4

The deepest heading we test here.

## Lists

A regular enumerated list:

1. Top Item 1
2. Top Item 2
    1. Nested Item 1
3. Top Item 3

A lettered list with a nested roman sublist:

a. First top-level item
b. Second top-level item
    i. Nested roman item one
    ii. Nested roman item two
c. Third top-level item

A bullet list for comparison:

- Alpha
- Bravo
    - Nested bullet
    - Another nested bullet
- Charlie

## Table

| Model    | Status      | Owner    |
|:---------|:-----------:|---------:|
| ModelA   | Released    | Person A |
| ModelB   | In progress | Person B |
| ModelC   | Planned     | Person C |

(Left-aligned, centered, and right-aligned columns.)

## Blockquote

> This is a blockquote. It tests the Block Text / Quote style in the reference
> template. It can span multiple lines.

## Code Block

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("world"))
```

## Footnote

Here is a sentence with a footnote reference.[^1]

[^1]: This is the footnote text. It tests the Footnote Reference and Footnote Text styles.
