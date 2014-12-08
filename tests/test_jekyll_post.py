# -*- coding: utf-8 -*-
import unittest

import jekyll2nikola.jekyll2nikola as SUT  # Subject Under Test


SIMPLE = """---
- title: my title
- description: my description
---
document
"""

TEASER_MD = """---
- title: another title
---
teaser
<!-- more -->
document
---
"""

TEASER_RST = """---
- title: another title
---
teaser
.. more
document
---
"""

class JekyllPostTest(unittest.TestCase):
    def test_read_properties_simple(self):
        reader = SUT.JekyllPost('foo.md', SIMPLE)
        self.assertEqual('my title', reader.metadata['title'])
        self.assertEqual('document', reader.document)

    def test_read_teaser_when_no_teasermark_returns_the_doc(self):
        reader = SUT.JekyllPost('foo.md', SIMPLE)
        self.assertEqual('document', reader.teaser)

    def test_read_document_when_no_teasermark_returns_empty(self):
        reader = SUT.JekyllPost('foo.md', SIMPLE)
        self.assertEqual('', reader.document_without_teaser)

    def test_read_teaser_markdown(self):
        reader = SUT.JekyllPost('foo.md', TEASER_MD)
        self.assertEqual('teaser\n', reader.teaser)

    def test_read_teaser_restructured_text(self):
        reader = SUT.JekyllPost('foo.md', TEASER_RST)
        self.assertEqual('teaser\n', reader.teaser)
