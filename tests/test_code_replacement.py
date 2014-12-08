# -*- coding: utf-8 -*-
import unittest

import jekyll2nikola.jekyll2nikola as SUT  # Subject Under Test


JEKYLL_CODE_BASIC = """
{% highlight %}
print("hello")
{% endhighlight %}
"""

RST_CODE_BASIC = """
.. code::

    print("hello")
"""

MARKDOWN_CODE_BASIC = """
```
print("hello")
```
"""

JEKYLL_CODE_LANG = """
{% highlight python %}
print("hello")
{% endhighlight %}
"""

RST_CODE_LANG = """
.. code:: python

    print("hello")
"""

MARKDOWN_CODE_LANG = """
```python
print("hello")
```
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

RST_CODE_ADV = """
.. code:: python

    print("hello")
"""

MARKDOWN_CODE_ADV = """
```python
print("hello")
```
"""


class JekyllDirectiveReplacement(unittest.TestCase):
    def test_code_replacement(self):
        repl = SUT.JekyllFilter(JEKYLL_CODE_BASIC)
        repl.replace()
        self.assertEqual(RST_CODE_BASIC, repl.content)

    def test_code_replacement_with_lang(self):
        repl = SUT.JekyllFilter(JEKYLL_CODE_LANG)
        repl.replace()
        self.assertEqual(RST_CODE_LANG, repl.content)

    def test_code_replacement_with_lang_and_properties_1(self):
        repl = SUT.JekyllFilter(JEKYLL_CODE_ADV_1)
        repl.replace()
        self.assertEqual(RST_CODE_ADV, repl.content)

    def test_code_replacement_with_lang_and_properties_2(self):
        repl = SUT.JekyllFilter(JEKYLL_CODE_ADV_2)
        repl.replace()
        self.assertEqual(RST_CODE_ADV, repl.content)


class JekyllDirectiveReplacementMarkdown(unittest.TestCase):
    def test_code_replacement(self):
        repl = SUT.MarkdownJekyllFilter(JEKYLL_CODE_BASIC)
        repl.replace()
        self.assertEqual(MARKDOWN_CODE_BASIC, repl.content)

    def test_code_replacement_with_lang(self):
        repl = SUT.MarkdownJekyllFilter(JEKYLL_CODE_LANG)
        repl.replace()
        self.assertEqual(MARKDOWN_CODE_LANG, repl.content)

    def test_code_replacement_with_lang_and_properties_1(self):
        repl = SUT.MarkdownJekyllFilter(JEKYLL_CODE_ADV_1)
        repl.replace()
        self.assertEqual(MARKDOWN_CODE_ADV, repl.content)

    def test_code_replacement_with_lang_and_properties_2(self):
        repl = SUT.MarkdownJekyllFilter(JEKYLL_CODE_ADV_2)
        repl.replace()
        self.assertEqual(MARKDOWN_CODE_ADV, repl.content)


class LinkReplacementTest(unittest.TestCase):
    def test_link_replacement(self):
        repl = SUT.JekyllFilter("{% post_url foo/bar %}")
        repl.replace()
        self.assertEqual('link://slug/foo/bar', repl.content)

    def test_link_replacement_with_mapping(self):
        repl = SUT.JekyllFilter("{% post_url foo/bar %}", {'foo/bar': 'bazz'})
        repl.replace()
        self.assertEqual('link://slug/bazz', repl.content)
