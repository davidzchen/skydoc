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

import unittest
import tempfile
# internal imports

from skydoc import common


class CommonTest(unittest.TestCase):
  """Unit tests for common functions."""

  def test_rule_doc_only(self):
    docstring = 'Rule documentation only docstring.'
    extracted_docs = common.parse_docstring(docstring)
    self.assertEqual('Rule documentation only docstring.', extracted_docs.doc)
    self.assertDictEqual({}, extracted_docs.attr_docs)
    self.assertEqual('', extracted_docs.example_doc)
    self.assertDictEqual({}, extracted_docs.output_docs)

  def test_rule_and_attribute_doc(self):
    docstring = (
        'Rule and attribute documentation.\n'
        '\n'
        'Args:\n'
        '  name: A unique name for this rule.\n'
        '  visibility: The visibility of this rule.\n')
    expected_attrs = {
        'name': 'A unique name for this rule.',
        'visibility': 'The visibility of this rule.'
    }

    extracted_docs = common.parse_docstring(docstring)
    self.assertEqual('Rule and attribute documentation.', extracted_docs.doc)
    self.assertDictEqual(expected_attrs, extracted_docs.attr_docs)
    self.assertEqual('', extracted_docs.example_doc)
    self.assertDictEqual({}, extracted_docs.output_docs)

  def test_multi_line_doc(self):
    docstring = (
        'Multi-line rule and attribute documentation.\n'
        '\n'
        'Rule doc continued here.\n'
        '\n'
        'Args:\n'
        '  name: A unique name for this rule.\n'
        '\n'
        '    Documentation for name continued here.\n'
        '  visibility: The visibility of this rule.\n'
        '\n'
        '    Documentation for visibility continued here.\n')
    expected_doc = (
        'Multi-line rule and attribute documentation.\n'
        '\n'
        'Rule doc continued here.')
    expected_attrs = {
        'name': ('A unique name for this rule.\n\n'
            'Documentation for name continued here.'),
        'visibility': ('The visibility of this rule.\n\n'
            'Documentation for visibility continued here.')
    }

    extracted_docs = common.parse_docstring(docstring)
    self.assertEqual(expected_doc, extracted_docs.doc)
    self.assertDictEqual(expected_attrs, extracted_docs.attr_docs)
    self.assertEqual('', extracted_docs.example_doc)
    self.assertDictEqual({}, extracted_docs.output_docs)

  def test_invalid_args(self):
    docstring = (
        'Rule and attribute documentation.\n'
        '\n'
        'Foo:\n'
        '  name: A unique name for this rule.\n'
        '  visibility: The visibility of this rule.\n')

    extracted_docs = common.parse_docstring(docstring)
    self.assertEqual(docstring.strip(), extracted_docs.doc)
    self.assertDictEqual({}, extracted_docs.attr_docs)
    self.assertEqual('', extracted_docs.example_doc)
    self.assertDictEqual({}, extracted_docs.output_docs)

  def test_example(self):
    docstring = (
        'Documentation with example\n'
        '\n'
        'Examples:\n'
        '  An example of how to use this rule:\n'
        '\n'
        '      example_rule()\n'
        '\n'
        '  Note about this example.\n'
        '\n'
        'Args:\n'
        '  name: A unique name for this rule.\n'
        '  visibility: The visibility of this rule.\n')
    expected_attrs = {
        'name': 'A unique name for this rule.',
        'visibility': 'The visibility of this rule.'
    }
    expected_example_doc = (
        'An example of how to use this rule:\n'
        '\n'
        '    example_rule()\n'
        '\n'
        'Note about this example.')

    extracted_docs = common.parse_docstring(docstring)
    self.assertEqual('Documentation with example', extracted_docs.doc)
    self.assertDictEqual(expected_attrs, extracted_docs.attr_docs)
    self.assertEqual(expected_example_doc, extracted_docs.example_doc)
    self.assertDictEqual({}, extracted_docs.output_docs)

  def test_example_after_attrs(self):
    docstring = (
        'Documentation with example\n'
        '\n'
        'Args:\n'
        '  name: A unique name for this rule.\n'
        '  visibility: The visibility of this rule.\n'
        '\n'
        'Examples:\n'
        '  An example of how to use this rule:\n'
        '\n'
        '      example_rule()\n'
        '\n'
        '  Note about this example.\n')
    expected_attrs = {
        'name': 'A unique name for this rule.',
        'visibility': 'The visibility of this rule.'
    }
    expected_example_doc = (
        'An example of how to use this rule:\n'
        '\n'
        '    example_rule()\n'
        '\n'
        'Note about this example.')

    extracted_docs = common.parse_docstring(docstring)
    self.assertEqual('Documentation with example', extracted_docs.doc)
    self.assertDictEqual(expected_attrs, extracted_docs.attr_docs)
    self.assertEqual(expected_example_doc, extracted_docs.example_doc)
    self.assertDictEqual({}, extracted_docs.output_docs)

  def test_outputs(self):
    docstring = (
        'Documentation with outputs\n'
        '\n'
        'Args:\n'
        '  name: A unique name for this rule.\n'
        '  visibility: The visibility of this rule.\n'
        '\n'
        'Outputs:\n'
        '  %{name}.jar: A Java archive.\n'
        '  %{name}_deploy.jar: A Java archive suitable for deployment.\n'
        '\n'
        '      Only built if explicitly requested.\n')
    expected_attrs = {
        'name': 'A unique name for this rule.',
        'visibility': 'The visibility of this rule.'
    }
    expected_outputs = {
        '%{name}.jar': 'A Java archive.',
        '%{name}_deploy.jar': ('A Java archive suitable for deployment.\n\n'
                               'Only built if explicitly requested.'),
    }

    extracted_docs = common.parse_docstring(docstring)
    self.assertEqual('Documentation with outputs', extracted_docs.doc)
    self.assertDictEqual(expected_attrs, extracted_docs.attr_docs)
    self.assertEqual('', extracted_docs.example_doc)
    self.assertDictEqual(expected_outputs, extracted_docs.output_docs)

  def check_renames(self, contents, expected_renames):
    with tempfile.NamedTemporaryFile() as tf:
      tf.write(contents)
      tf.flush()

      renames = common.read_renames(tf.name)
      self.assertDictEqual(expected_renames, renames)

  def invalid_renames(self, contents):
    with tempfile.NamedTemporaryFile() as tf:
      tf.write(contents)
      tf.flush()

      self.assertRaises(common.InputError, common.read_renames, tf.name)

  def test_read_renames(self):
    self.check_renames('', {})
    self.check_renames(
        'rules/checkstyle.bzl\tcheckstyle.md\n'
        'rules/rat.bzl\trat.md\n',
        {
            'rules/checkstyle.bzl': 'checkstyle.md',
            'rules/rat.bzl': 'rat.md',
        })

    self.invalid_renames('rules/checkstyle.bzl\n')
    self.invalid_renames('rules/checkstyle.bzl\t\n')
    self.invalid_renames('\trules/checkstyle.bzl\n')

  def test_replace_extension(self):
    self.assertEqual('foo.md', common.replace_extension('foo.bzl', 'md'))
    self.assertEqual('foo.bzl.md',
                     common.replace_extension('foo.bzl.bzl', 'md'))
    self.assertEqual('foo', common.replace_extension('foo', 'md'))

  def rename_conflict(self, renames, bzl_files, format):
    self.assertRaises(common.InputError,
                      common.validate_renames,
                      renames,
                      bzl_files,
                      format)

  def test_validate_renames(self):
    common.validate_renames({}, ['foo/foo.bzl', 'bar.bzl'], 'markdown')
    common.validate_renames({'foo/bar.bzl': 'foo.md'},
                            ['foo/bar.bzl', 'bar.bzl'], 'markdown')
    common.validate_renames({'foo/foo.bzl': 'bar.md'},
                            ['foo/foo.bzl', 'bar.bzl'], 'html')

    self.rename_conflict({}, ['foo/bar.bzl', 'bar.bzl'], 'markdown')
    self.rename_conflict({'foo/foo.bzl': 'bar.md'},
                         ['foo/foo.bzl', 'bar.bzl'], 'markdown')
    self.rename_conflict({'foo/foo.bzl': 'baz.md', 'bar.bzl': 'baz.md'},
                         ['foo/foo.bzl', 'bar.bzl'], 'markdown')

if __name__ == '__main__':
  unittest.main()
