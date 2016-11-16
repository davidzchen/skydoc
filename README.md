# [Skydoc](https://skydoc.bazel.build) - Skylark Documentation Generator

[![Build Status](http://ci.bazel.io/buildStatus/icon?job=skydoc)](http://ci.bazel.io/job/skydoc/)

Skydoc is a documentation generator for [Bazel](https://bazel.build) build rules
written in [Skylark](https://bazel.build/docs/skylark/index.html).

Skydoc provides a set of Skylark rules (`skylark_library` and `skylark_doc`)
that can be used to build documentation for Skylark rules in either Markdown or
HTML. Skydoc generates one documentation page per `.bzl` file.

![A screenshot of Skydoc generated HTML documentation](https://raw.githubusercontent.com/bazelbuild/skydoc/master/skydoc-screenshot.png)

## Get Started

* How to [set up Skydoc for your project](https://skydoc.bazel.build/docs/getting_started.html)
* The Skydoc [docstring format](https://skydoc.bazel.build/docs/writing.html)
* How to [integrate Skydoc with your build](https://skydoc.bazel.build/docs/generating.html).

## About Skydoc

* How to [contribute to Skydoc](https://skydoc.bazel.build/contributing.html)
* See the [Skydoc roadmap](https://skydoc.bazel.build/roadmap.html)
