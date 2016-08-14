---
layout: default
title: Advanced Features
---

## Renaming Files

Suppose you have a project containing a number of `.bzl` files containing
Skylark rules:

```
[workspace]/
    WORKSPACE
    rules/
        BUILD
        checkstyle.bzl
        rat.bzl
```

Suppose you wish to specify the names of the Markdown or HTML files generated
from the `.bzl` files. To do so, you can use the `rename` attribute, which takes
a `string_dict` where the keys are the labels for the input `.bzl` files
relative to the package and the values are the names of the output files.

`BUILD`:

```python
load("@io_bazel_skydoc//skylark:skylark.bzl", "skylark_doc")

skylark_doc(
    name = "docs",
    srcs = [
        "checkstyle.bzl",
        "rat.bzl",
    ],
    rename = {
        "checkstyle.bzl": "checkstyle_rules.md",
        "rat.bzl": "rat_rules.md",
    },
)
```

Running `bazel build //rules:docs`, the documentation file for `checkstyle.bzl`
will be generated as `checkstyle_rules.md` in the output ZIP archive and
similarly for `rat.bzl`.
