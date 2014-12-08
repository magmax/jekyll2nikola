#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import yaml
import re
import argparse
import logging
import csv
import datetime
from dateutil import parser as dateparser


logger = logging.getLogger(__name__)


class Jekyll2NikolaError(Exception):
    pass


class UnsupportedFileType(Jekyll2NikolaError):
    def __init__(self, ext, *args, **kwargs):
        super(UnsupportedFileType, self).__init__(self)
        self._ext = ext

    def __str__(self):
        return 'Unsupported file type "%s"' % self._ext


class UnsupportedMetadataType(Jekyll2NikolaError):
    def __init__(self, metadata, *args, **kwargs):
        super(UnsupportedMetadataType, self).__init__(self)
        self._metadata = metadata

    def __str__(self):
        return 'Unsupported metadata type "%s"' % type(self._metadata)


class IntelligentMeta(object):
    def __init__(self, filename, metadata):
        if isinstance(metadata, list):
            self._meta = {}
            for item in metadata:
                key = item.keys()[0]
                value = item[key]
                self._meta[key] = value
        elif isinstance(metadata, dict):
            self._meta = metadata
        else:
            raise UnsupportedMetadataType(metadata)

        self._filename = filename

    @property
    def keys(self):
        return self._meta.keys()

    def __getitem__(self, key):
        if key in self._meta and key is not 'date':
            return self._meta[key]

        method = self._EXTRACTORS.get(key)
        if method:
            return method(self)

    def _extract_title(self):
        regex = (
            r'(?:\d+-\d+-\d+-)'
            r'(?P<name>.+?)'
            r'(?:\.\w+)?$'
        )
        m = re.match(regex, self._filename)
        if m is None:
            return None
        name = m.group('name')
        return name

    def _extract_slug(self):
        title = self['title']
        return re.sub(r'\W', '_', title)

    def _extract_date(self):
        raw_date = self._meta.get('date')
        if isinstance(raw_date, datetime.date):
            return raw_date
        if isinstance(raw_date, str):
            return dateparser.parse(raw_date)

        # date not in metadata or unreadable. Trying from filename.
        raw_date = re.findall(r'\d+\-\d+\-\d+', self._filename)
        if raw_date:
            return dateparser.parse(raw_date[0])
        logger.warning('Unknown date "%s". Using today.', raw_date)
        return datetime.date.today()

    _EXTRACTORS = {
        'title': _extract_title,
        'slug': _extract_slug,
        'date': _extract_date,
    }


class JekyllPost(object):
    def __init__(self, path, content):
        self._content = content
        self._path = path

    @property
    def metadata(self):
        docs = yaml.load_all(self._content)
        metadata = docs.next()
        filename = os.path.basename(self._path)
        return IntelligentMeta(filename, metadata)

    @property
    def document(self):
        foo = yaml.compose_all(self._content)
        composer = foo.next()
        last_line = composer.end_mark.line + 1
        return '\n'.join(self._content.splitlines()[last_line:])

    @property
    def teaser(self):
        document = self.document
        end = self._find_teaser_end(document)
        return document[:end.start()] if end else self.document

    @property
    def document_without_teaser(self):
        document = self.document
        end = self._find_teaser_end(document)
        return document[document.find('\n', end.end()) + 1:] if end else ''

    def _find_teaser_end(self, document):
        return re.search(r'<!--\s*more\s*-->|..\s+more', document)


class JekyllFilter(object):
    REGEX_CODE = (
        r'\{%\s*highlight\s*(?P<lang>\w+)?'
        r'(?P<props>\s*(?:linenos|linenos=\w+|hl_lines|hl_lines=\S+))*\s*%\}'
        r'(?P<code>.*?)'
        r'\{%\s*endhighlight\s*%\}'
    )
    REGEX_LINK = (
        r'{%' r'\s*'
        r'post_url' r'\s*'
        r'(?P<url>.*?)' r'\s*'
        r'%}'
    )

    def __init__(self, content, link_map=None):
        self.content = content
        self._link_map = link_map or dict()

    def replace(self):
        self._replace_code()
        self._replace_links()

    def get_internal_refs(self):
        return re.findall(self.REGEX_LINK, self.content)

    def _replace_code(self):
        def code_repl(matchobj):
            lang = matchobj.group('lang')
            code = matchobj.group('code')
            return self._code_surround(lang, code)
        self.content = re.sub(self.REGEX_CODE, code_repl, self.content,
                              flags=re.MULTILINE | re.DOTALL)

    def _replace_links(self):
        def link_repl(matchobj):
            url = matchobj.group('url')
            if url not in self._link_map:
                logger.warning('Slug not found for url %s', url)
            return 'link://slug/%s' % self._link_map.get(url, url)
        self.content = re.sub(self.REGEX_LINK, link_repl, self.content)

    def _code_surround(self, lang, code):
        return '.. code::%s\n%s' % (
            ' %s' % lang if lang else '',
            '\n'.join(('    ' + s if s.strip() else '')
                      for s in code.splitlines())
        )


class MarkdownJekyllFilter(JekyllFilter):
    def _code_surround(self, lang, code):
        return '```%s%s```' % (lang.strip() if lang else '', code)


class NikolaWriter(object):
    def __init__(self, filename, reader):
        self.filename = filename
        self.reader = reader
        self._fd = None

    def write(self):
        logger.debug('Writing file %s', self.filename)
        path = os.path.dirname(self.filename)
        if not os.path.exists(path):
            os.makedirs(path)
        with open(self.filename, 'w+') as fd:
            self._fd = fd
            self.write_metadata()
            self.write_teaser()
            self.write_teaser_delimiter()
            self.write_content()

    def write_metadata(self):
        """Overrideable."""
        meta = self.reader.metadata
        mandatory = ('title', 'slug', 'date')
        for key in mandatory:
            self.write_metadata_line(key, meta[key])
        for key in meta.keys:
            if key not in mandatory:
                self.write_metadata_line(key, meta[key])

    def write_metadata_line(self, key, value):
        try:
            self._fd.write('.. %s: %s\n' % (key, value))
        except UnicodeEncodeError:
            self._fd.write('.. %s: %s\n' % (key, value.encode('utf-8')))

    def write_teaser(self):
        self._fd.write(self.reader.teaser)

    def write_teaser_delimiter(self):
        self._fd.write('.. TEASER_END\n')

    def write_content(self):
        self._fd.write(self.reader.document_without_teaser)


class MarkdownNikolaWriter(NikolaWriter):
    def write_teaser_delimiter(self):
        self._fd.write('<!-- TEASER_END -->')

    def write_metadata(self):
        self._fd.write('<!--\n')
        super(MarkdownNikolaWriter, self).write_metadata()
        self._fd.write('-->\n')


class FileWalker(object):
    def __init__(self, root, recursive):
        self._root = root
        self._recursive = recursive

    def process(self, operation, *args, **kwargs):
        if os.path.isdir(self._root):
            for filename in self._filelist():
                self._run(operation, filename, *args, **kwargs)
        elif os.path.isfile(self._root):
            self._run(operation, self._root, *args, **kwargs)
        else:
            logger.info(
                'File "%s" is not a file or directory and will be ignored'
                % self._root
            )

    def _run(self, operation, *args, **kwargs):
        try:
            operation(*args, **kwargs)
        except UnsupportedFileType as e:
            logger.debug(e)

    def _filelist(self):
        if self._recursive:
            for dirpath, dirnames, filenames in os.walk(self._root):
                for filename in filenames:
                    yield os.path.join(dirpath, filename)
        else:
            for filename in os.listdir(self._root):
                path = os.path.join(self._root, filename)
                if os.path.isfile(path):
                    yield path
                else:
                    logging.debug('Ignoring directory "%s"', path)


def setup_logging(verbose):
    if verbose:
        FORMAT = '%(asctime)-15s %(levelname)-8s %(message)s'
        LEVEL = logging.DEBUG
    else:
        FORMAT = '%(levelname)-8s %(message)s'
        LEVEL = logging.INFO
    logging.basicConfig(format=FORMAT)
    logger.setLevel(LEVEL)


def load_link_map(filename):
    result = dict()
    if not os.path.exists(filename):
        logger.debug('Link map file "%s" not found', filename)
        return result
    with open(filename) as fd:
        for row in csv.reader(fd, delimiter='='):
            if len(row) < 2:
                continue
            result[row[0].strip()] = row[1].strip()
    return result


def get_links(filename, links):
    logger.debug('Getting links for file %s', filename)
    if filename.endswith(('.md', '.markdown')):
        FilterClass = MarkdownJekyllFilter
    else:
        FilterClass = JekyllFilter

    with open(filename) as fd:
        content = fd.read()
    jekyll_filter = FilterClass(content)
    links.extend(jekyll_filter.get_internal_refs())


def import_file(path, output, link_map):
    logger.debug('Importing file %s', path)
    if path.endswith(('.md', '.markdown')):
        WriterClass = MarkdownNikolaWriter
        FilterClass = MarkdownJekyllFilter
    else:
        WriterClass = NikolaWriter
        FilterClass = JekyllFilter

    with open(path) as fd:
        content = fd.read()
    jekyll_reader = JekyllPost(path, content)
    jekyll_filter = FilterClass(content, link_map)
    jekyll_filter.replace()

    filename = os.path.basename(path)
    metadata = IntelligentMeta(filename, jekyll_reader.metadata)
    date = metadata['date']
    output_file = os.path.join(output, str(date.year), str(date.month),
                               filename)
    writer = WriterClass(output_file, jekyll_reader)
    writer.write()
    logger.info('File %s imported!', path)


def main():
    parser = argparse.ArgumentParser(
        description='Import Jekyll/Octopress posts')
    parser.add_argument('operation', choices=('get_links', 'import'),
                        help='Retrieve the internal links')
    parser.add_argument('-f', '--from', dest='source', default='.',
                        help='Path to take files from')
    parser.add_argument('-t', '--to', dest='sink', default='output',
                        help='Path to take files from')
    parser.add_argument('-r', '--recursive', action="store_true",
                        default=False,
                        help='Recursive for directories')
    parser.add_argument('-l', '--link-file', dest='linkfile', default='links',
                        help='File with mappings links=slug')
    parser.add_argument('-v', '--verbose', action="store_true", default=False,
                        help='More verbose logs')

    args = parser.parse_args()

    setup_logging(args.verbose)

    links = []
    walker = FileWalker(args.source, args.recursive)
    if args.operation == 'get_links':
        walker.process(get_links, links)
        print '\n'.join(sorted(set(links)))
    elif args.operation == 'import':
        link_map = load_link_map(args.linkfile)
        walker.process(import_file, args.sink, link_map)


if __name__ == '__main__':
    main()
