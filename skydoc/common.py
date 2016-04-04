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

"""Common functions for skydoc."""

import re
from src.main.protobuf import build_pb2
from xml.sax.saxutils import escape


def leading_whitespace(line):
  return len(line) - len(line.lstrip())

def _parse_attribute_docs(attr_docs, line, it):
  attr_docs = {}  # Dictionary for attribute documentation
  attr = None  # Current attribute name
  desc = None  # Description for current attribute
  args_leading_ws = leading_whitespace(line)
  for line in it:
    # If a blank line is encountered, we have finished parsing the "Args"
    # section.
    if line.strip() and leading_whitespace(line) == args_leading_ws:
      break
    # In practice, users sometimes add a "-" prefix, so we strip it even
    # though it is not recommended by the style guide
    match = re.search(r"^\s*-?\s*(\w+):\s*(.*)", line)
    if match:  # We have found a new attribute
      if var:
        attr_docs[var] = escape(desc)
      var, desc = match.group(1), match.group(2)
    elif var:
      # Merge documentation when it is multiline
      desc = desc + "\n" + line.strip()

  if attr:
    attr_docs[attr] = escape(desc)
  return attr_docs

def _parse_example_docs(examples, line, it):
  pass

def _parse_implicit_output_docs(implicit_outputs, line, it)
  pass

ARGS_HEADING = "Args:"
EXAMPLES_HEADING = "Examples:"
IMPLICIT_OUTPUTS_HEADING = "Implicit Outputs:"

def parse_attribute_doc(doc):
  """Analyzes the documentation string for attributes.

  This looks for the "Args:" separator to fetch documentation for each
  attribute. The "Args" section ends at the first blank line.

  Args:
    doc: The documentation string

  Returns:
    The new documentation string and a dictionary that maps each attribute to
    its documentation
  """
  attr_docs = {}
  examples = []
  implicit_outputs = {}
  lines = doc.split("\n")
  docs = []
  it = iter(lines)
  for line in it:
    if line.strip() == ARGS_HEADING:
      _parse_attribute_docs(attr_docs, line, it)
      continue
    elif line.strip() == EXAMPLES_HEADING:
      _parse_example_docs(examples, line, it)
      continue
    elif line.strip() == IMPLICIT_OUTPUTS_HEADING:
      _parse_implicit_output_docs(implicit_outputs, line, it)
      continue

    docs.append(line)

  doc = "\n".join(docs)
  return doc, attr_docs
