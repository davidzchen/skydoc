# Copyright 2016 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Skylark rules"""

_SKYLARK_FILETYPE = FileType([".bzl"])

ZIP_PATH = "/usr/bin/zip"

def _get_transitive_sources(deps):
  """Collects source files of transitive dependencies."

  Args:
    deps: List of deps labels from ctx.attr.deps.

  Returns:
    Returns a list of Files containing sources of transitive dependencies.
  """
  transitive_sources = set(order="compile")
  for dep in deps:
    transitive_sources += dep.transitive_bzl_files
  return transitive_sources

def _get_renames(ctx):
  renames = {}
  for dep in ctx.attr.deps:
    renames.update(dep.transitive_renames)

  for (key, value) in ctx.attr.rename.items():
    resolved_key = "%s/%s" % (ctx.label.package, key)
    renames[resolved_key] = value
  return renames

def _skylark_library_impl(ctx):
  """Implementation of the skylark_library rule."""
  sources = _get_transitive_sources(ctx.attr.deps) + ctx.files.srcs
  renames = _get_renames(ctx)
  return struct(files = set(),
                transitive_bzl_files = sources,
                transitive_renames = renames)

def _skydoc(ctx):
  for f in ctx.files.skydoc:
    if not f.path.endswith(".py"):
      return f

def _serialize_renames(renames):
  contents = ""
  for (key, value) in renames.items():
    contents += "%s\t%s\n" % (key, value)
  return contents

def _skylark_doc_impl(ctx):
  """Implementation of the skylark_doc rule."""
  # Write renames file.
  renames = _get_renames(ctx)
  renames_file = None
  if len(renames) > 0:
    renames_file = ctx.new_file(ctx.label.name + ".renames")
    ctx.file_action(renames_file, _serialize_renames(renames))

  # Generate documentation archive.
  skylark_doc_zip = ctx.outputs.skylark_doc_zip
  inputs = _get_transitive_sources(ctx.attr.deps) + ctx.files.srcs
  sources = [source.path for source in inputs]
  args = [
      "--format=%s" % ctx.attr.format,
      "--output_file=%s" % ctx.outputs.skylark_doc_zip.path,
  ]
  if renames_file and len(renames) > 0:
    args += ["--rename=%s" % renames_file.path]
    inputs += [renames_file]
  args += sources
  skydoc = _skydoc(ctx)
  ctx.action(
      inputs = list(inputs) + [skydoc],
      executable = skydoc,
      arguments = args,
      outputs = [skylark_doc_zip],
      mnemonic = "Skydoc",
      use_default_shell_env = True,
      progress_message = ("Generating Skylark doc for %s (%d files)"
                          % (ctx.label.name, len(sources))))

_skylark_common_attrs = {
    "srcs": attr.label_list(allow_files = _SKYLARK_FILETYPE),
    "deps": attr.label_list(
        providers = ["transitive_bzl_files", "transitive_renames"],
        allow_files = False),
    "rename": attr.string_dict(),
}

skylark_library = rule(
    _skylark_library_impl,
    attrs = _skylark_common_attrs,
)
"""Creates a logical collection of Skylark .bzl files.

Args:
  srcs: List of `.bzl` files that are processed to create this target.
  deps: List of other `skylark_library` targets that are required by the Skylark
    files listed in `srcs`.
  rename: Dictionary of files to rename. The key is the label of the .bzl file
    relative to the package this rule is in, and the value is the desired output
    filename.

Example:
  If you would like to generate documentation for multiple .bzl files in various
  packages in your workspace, you can use the `skylark_library` rule to create
  logical collections of Skylark sources and add a single `skylark_doc` target
  for building documentation for all of the rule sets.

  Suppose your project has the following structure:

  ```
  [workspace]/
      WORKSPACE
      BUILD
      checkstyle/
          BUILD
          checkstyle.bzl
      lua/
          BUILD
          lua.bzl
          luarocks.bzl
  ```

  In this case, you can have `skylark_library` targets in `checkstyle/BUILD` and
  `lua/BUILD`:

  `checkstyle/BUILD`:

  ```python
  load("@io_bazel_skydoc//skylark:skylark.bzl", "skylark_library")

  skylark_library(
      name = "checkstyle-rules",
      srcs = ["checkstyle.bzl"],
  )
  ```

  `lua/BUILD`:

  ```python
  load("@io_bazel_skydoc//skylark:skylark.bzl", "skylark_library")

  skylark_library(
      name = "lua-rules",
      srcs = [
          "lua.bzl",
          "luarocks.bzl",
      ],
  )
  ```

  To build documentation for all the above `.bzl` files at once:

  `BUILD`:

  ```python
  load("@io_bazel_skydoc//skylark:skylark.bzl", "skylark_doc")

  skylark_doc(
      name = "docs",
      deps = [
          "//checkstyle:checkstyle-rules",
          "//lua:lua-rules",
      ],
  )
  ```

  Running `bazel build //:docs` would build a single zip containing documentation
  for all the `.bzl` files contained in the two `skylark_library` targets.
"""

_skylark_doc_attrs = {
    "format": attr.string(default = "markdown"),
    "skydoc": attr.label(
        default = Label("//skydoc"),
        cfg = HOST_CFG,
        executable = True),
}

skylark_doc = rule(
    _skylark_doc_impl,
    attrs = dict(_skylark_common_attrs.items() + _skylark_doc_attrs.items()),
    outputs = {
        "skylark_doc_zip": "%{name}-skydoc.zip",
    },
)
"""Generates Skylark rule documentation.

Args:
  srcs: List of `.bzl` files that are processed to create this target.
  deps: List of other `skylark_library` targets that are required by the Skylark
    files listed in `srcs`.
  rename: Dictionary of files to rename. The key is the label of the .bzl file
    relative to the package this rule is in, and the value is the desired output
    filename.
  format: The type of output to generate. Possible values are `"markdown"` and
    `"html"`.

Outputs:
  skylark_doc_zip: A zip file containing the generated documentation.

Example:
  Suppose you have a project containing Skylark rules you want to document:

  ```
  [workspace]/
      WORKSPACE
      checkstyle/
          BUILD
          checkstyle.bzl
  ```

  To generate documentation for the rules and macros in `checkstyle.bzl`, add the
  following target to `rules/BUILD`:

  ```python
  load("@io_bazel_skydoc//skylark:skylark.bzl", "skylark_doc")

  skylark_doc(
      name = "checkstyle-docs",
      srcs = ["checkstyle.bzl"],
  )
  ```

  Running `bazel build //checkstyle:checkstyle-docs` will generate a zip file
  containing documentation for the public rules and macros in `checkstyle.bzl`.

  By default, Skydoc will generate documentation in Markdown. To generate
  a set of HTML pages that is ready to be served, set `format = "html"`.
"""

JINJA2_BUILD_FILE = """
py_library(
    name = "jinja2",
    srcs = glob(["jinja2/*.py"]),
    srcs_version = "PY2AND3",
    deps = [
        "@markupsafe_archive//:markupsafe",
    ],
    visibility = ["//visibility:public"],
)
"""

MARKUPSAFE_BUILD_FILE = """
py_library(
    name = "markupsafe",
    srcs = glob(["markupsafe/*.py"]),
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
)
"""

MISTUNE_BUILD_FILE = """
py_library(
    name = "mistune",
    srcs = ["mistune.py"],
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
)
"""

SIX_BUILD_FILE = """
py_library(
    name = "six",
    srcs = ["six.py"],
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
)
"""

GFLAGS_BUILD_FILE = """
py_library(
    name = "gflags",
    srcs = [
        "gflags.py",
        "gflags_validators.py",
    ],
    visibility = ["//visibility:public"],
)
"""

def skydoc_repositories():
  """Adds the external repositories used by the skylark rules."""
  native.git_repository(
      name = "protobuf",
      remote = "https://github.com/google/protobuf.git",
      commit = "ed87c1fe2c6e1633cadb62cf54b2723b2b25c280",
  )

  # Protobuf expects an //external:python_headers label which would contain the
  # Python headers if fast Python protos is enabled. Since we are not using fast
  # Python protos, bind python_headers to a dummy target.
  native.bind(
      name = "python_headers",
      actual = "//:dummy",
  )

  native.new_http_archive(
      name = "markupsafe_archive",
      url = "https://pypi.python.org/packages/source/M/MarkupSafe/MarkupSafe-0.23.tar.gz#md5=f5ab3deee4c37cd6a922fb81e730da6e",
      sha256 = "a4ec1aff59b95a14b45eb2e23761a0179e98319da5a7eb76b56ea8cdc7b871c3",
      build_file_content = MARKUPSAFE_BUILD_FILE,
      strip_prefix = "MarkupSafe-0.23",
  )

  native.bind(
      name = "markupsafe",
      actual = "@markupsafe_archive//:markupsafe",
  )

  native.new_http_archive(
      name = "jinja2_archive",
      url = "https://pypi.python.org/packages/source/J/Jinja2/Jinja2-2.8.tar.gz#md5=edb51693fe22c53cee5403775c71a99e",
      sha256 = "bc1ff2ff88dbfacefde4ddde471d1417d3b304e8df103a7a9437d47269201bf4",
      build_file_content = JINJA2_BUILD_FILE,
      strip_prefix = "Jinja2-2.8",
  )

  native.bind(
      name = "jinja2",
      actual = "@jinja2_archive//:jinja2",
  )

  native.new_http_archive(
      name = "mistune_archive",
      url = "https://pypi.python.org/packages/source/m/mistune/mistune-0.7.1.tar.gz#md5=057bc28bf629d6a1283d680a34ed9d0f",
      sha256 = "6076dedf768348927d991f4371e5a799c6a0158b16091df08ee85ee231d929a7",
      build_file_content = MISTUNE_BUILD_FILE,
      strip_prefix = "mistune-0.7.1",
  )

  native.bind(
      name = "mistune",
      actual = "@mistune_archive//:mistune",
  )

  native.new_http_archive(
      name = "six_archive",
      url = "https://pypi.python.org/packages/source/s/six/six-1.10.0.tar.gz#md5=34eed507548117b2ab523ab14b2f8b55",
      sha256 = "105f8d68616f8248e24bf0e9372ef04d3cc10104f1980f54d57b2ce73a5ad56a",
      build_file_content = SIX_BUILD_FILE,
      strip_prefix = "six-1.10.0",
  )

  native.bind(
      name = "six",
      actual = "@six_archive//:six",
  )

  native.new_git_repository(
      name = "gflags_repo",
      remote = "https://github.com/google/python-gflags",
      tag = "python-gflags-2.0",
      build_file_content = GFLAGS_BUILD_FILE,
  )

  native.bind(
      name = "gflags",
      actual = "@gflags_repo//:gflags",
  )
