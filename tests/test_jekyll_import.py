# -*- coding: utf-8 -*-
import unittest
import datetime
import sys
sys.path.append('scripts')

import octopress_import as SUT  # Subject Under Test


SIMPLE = """---
- title: my title
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

class JekyllReaderTest(unittest.TestCase):
    def test_read_properties_simple(self):
        reader = SUT.JekyllReader(SIMPLE)
        self.assertEqual([{'title': 'my title'}], reader.metadata)
        self.assertEqual('document', reader.document)

    def test_read_teaser_when_no_teasermark_returns_the_doc(self):
        reader = SUT.JekyllReader(SIMPLE)
        self.assertEqual('document', reader.teaser)

    def test_read_document_when_no_teasermark_returns_empty(self):
        reader = SUT.JekyllReader(SIMPLE)
        self.assertEqual('', reader.document_without_teaser)

    def test_read_teaser_markdown(self):
        reader = SUT.JekyllReader(TEASER_MD)
        self.assertEqual('teaser\n', reader.teaser)

    def test_read_teaser_restructured_text(self):
        reader = SUT.JekyllReader(TEASER_RST)
        self.assertEqual('teaser\n', reader.teaser)


JEKYLL_CODE_BASIC = """
{% highlight %}
print("hello")
{% endhighlight %}
"""

STANDARD_CODE_BASIC = """
.. code::

    print("hello")
"""

JEKYLL_CODE_LANG = """
{% highlight python %}
print("hello")
{% endhighlight %}
"""

STANDARD_CODE_LANG = """
.. code:: python

    print("hello")
"""

JEKYLL_CODE_ADV_1 = """
{% highlight python hl_lines=1,2 %}
print("hello")
{% endhighlight %}
"""

JEKYLL_CODE_ADV_2 = """
{% highlight python linenos %}
print("hello")
{% endhighlight %}
"""

STANDARD_CODE_ADV = """
.. code:: python

    print("hello")
"""


class JekyllDirectiveReplacement(unittest.TestCase):
    def test_code_replacement(self):
        repl = SUT.JekyllFilter(JEKYLL_CODE_BASIC)
        repl.replace()
        self.assertEqual(STANDARD_CODE_BASIC, repl.content)

    def test_code_replacement_with_lang(self):
        repl = SUT.JekyllFilter(JEKYLL_CODE_LANG)
        repl.replace()
        self.assertEqual(STANDARD_CODE_LANG, repl.content)

    def test_code_replacement_with_lang_and_properties_1(self):
        repl = SUT.JekyllFilter(JEKYLL_CODE_ADV_1)
        repl.replace()
        self.assertEqual(STANDARD_CODE_ADV, repl.content)

    def test_code_replacement_with_lang_and_properties_2(self):
        repl = SUT.JekyllFilter(JEKYLL_CODE_ADV_2)
        repl.replace()
        self.assertEqual(STANDARD_CODE_ADV, repl.content)

    def test_link_replacement(self):
        repl = SUT.JekyllFilter("{% post_url foo/bar %}")
        repl.replace()
        self.assertEqual('link://slug/foo/bar', repl.content)

    def test_link_replacement_with_mapping(self):
        repl = SUT.JekyllFilter("{% post_url foo/bar %}", {'foo/bar': 'bazz'})
        repl.replace()
        self.assertEqual('link://slug/bazz', repl.content)


class TestIntelligentMeta(unittest.TestCase):
    def test_no_previous_data(self):
        meta = SUT.IntelligentMeta('2012-01-01-foo.md', {})
        self.assertEqual('foo', meta['title'])
        self.assertEqual('foo', meta['slug'])

    def test_no_previous_data_tricky(self):
        meta = SUT.IntelligentMeta('2012-01-01-this is España.md', {})
        self.assertEqual('this is España', meta['title'])
        self.assertEqual('this_is_Espa__a', meta['slug'])

    def test_date(self):
        meta = SUT.IntelligentMeta('2012-01-01-foo.md', {})
        date = meta['date']
        self.assertIsInstance(date, datetime.date)
        self.assertEqual('2012-01-01 00:00:00', str(date))

    def test_today_if_no_date(self):
        meta = SUT.IntelligentMeta('foo.md', {})
        date = meta['date']
        self.assertIsInstance(date, datetime.date)
        self.assertEqual(datetime.date.today(), date)

    def test_previous_data(self):
        meta = SUT.IntelligentMeta('2012-01-01-foo.md',
                                   {'title': 'bar',
                                    'slug': 'bazz'})
        self.assertEqual('bar', meta['title'])
        self.assertEqual('bazz', meta['slug'])

    def test_previous_date(self):
        meta = SUT.IntelligentMeta('2012-01-01-foo.md',
                                   {'date': '2013-05-05'})
        self.assertEqual('2013-05-05 00:00:00', str(meta['date']))
