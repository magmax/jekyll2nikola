# -*- coding: utf-8 -*-
import unittest
import datetime

import jekyll2nikola.jekyll2nikola as SUT  # Subject Under Test


class TestIntelligentMeta(unittest.TestCase):
    def test_no_previous_data(self):
        meta = SUT.IntelligentMeta('2012-01-01-foo.md', {})
        self.assertEqual('foo', meta['title'])
        self.assertEqual('foo', meta['slug'])

    def test_no_previous_data_tricky(self):
        meta = SUT.IntelligentMeta('2012-01-01-this is España.md', {})
        self.assertEqual('this is España', meta['title'])
        assert (meta['slug'] in ('this_is_Espa__a', 'this_is_España'))

    def test_date(self):
        meta = SUT.IntelligentMeta('2012-01-01-foo.md', {})
        date = meta['date']
        self.assertIsInstance(date, datetime.date)
        self.assertEqual(datetime.date(2012, 1, 1), date.date())

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
        self.assertEqual(datetime.date(2013, 5, 5), meta['date'].date())
