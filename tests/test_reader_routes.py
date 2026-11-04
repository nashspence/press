"""Probe the actual citation and notice routes without network access."""
import hashlib
import io
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from asset_policy import AssetError
from reader_routes import verify_reader_routes


class ReaderRouteTests(unittest.TestCase):
    def setUp(self):
        self.tag = 'works/work/v1.0.0'
        self.url = 'https://press.test/' + self.tag
        self.target = 'https://github.com/owner/press/releases/tag'
        self.html = b'<h2 id="methods">Methods</h2>'
        self.manifest = {'tag': self.tag, 'record_url': self.url,
                         'source_commit': 'a' * 40, 'canonical_artifact': 'work-v1.0.0.html',
                         'html_sha256': hashlib.sha256(self.html).hexdigest()}
        self.notice = '2026-11-04 Withdrawal: The result is withdrawn.'
        self.page = ('<p>work-v1.0.0.html Source commit: ' + 'a' * 40 + '</p><ul><li>' +
                     self.notice + '</li></ul><a href="' + self.url + '/read">Read</a>')
        self.content = self.html
        self.disposition = 'inline'
        self.location = None
        self.calls = []
        self.enterContext(patch('reader_routes.public_response', self.response))
        self.enterContext(patch.dict('os.environ', {'RECORD_TARGET': ''}))

    @contextmanager
    def response(self, url, *args, **kwargs):
        self.calls.append(url)
        target = self.target + '/' + self.tag
        if url == self.url or (url == self.url + '/read' and not target.startswith('https://github.com/')):
            status, headers, data = 302, {'Location': self.location or target + url[len(self.url):]}, b''
        elif url == target:
            status, headers, data = 200, {'Content-Type': 'text/html'}, self.page.encode()
        elif url in {self.url + '/read', target + '/read'}:
            status, headers, data = 200, {'Content-Type': 'text/html', 'Content-Disposition': self.disposition}, self.content
        else:
            self.fail('unexpected destination ' + url)
        file = io.BytesIO(data)
        file.status = status
        file.getheader = headers.get
        yield file

    def check(self, **kwargs):
        verify_reader_routes(self.manifest, 'owner/press', notices=['- ' + self.notice], **kwargs)

    def test_citation_follows_exact_record_and_verifies_inline_bytes(self):
        self.check()
        self.assertEqual(self.calls, [self.url, self.target + '/' + self.tag, self.url + '/read'])
        self.location = 'https://other.test/' + self.tag
        with self.assertRaisesRegex(AssetError, 'temporary redirect'):
            self.check()

    def test_stale_and_invisible_withdrawal_are_detected(self):
        original = self.page
        for hidden in ['', '<script>' + self.notice + '</script>', '<details>' + self.notice + '</details>',
                       '<!--' + self.notice + '-->', '<div hidden><p>' + self.notice + '</p></div>']:
            self.page = original.replace(self.notice, hidden)
            with self.subTest(hidden=hidden), self.assertRaisesRegex(AssetError, 'committed notice'):
                self.check()

    def test_wrong_file_and_attachment_download_fail(self):
        self.content = b'<h2>Wrong edition</h2>'
        with self.assertRaisesRegex(AssetError, 'authorized edition bytes'):
            self.check()
        self.disposition = 'attachment; filename=work.html'
        with self.assertRaisesRegex(AssetError, 'inline HTML'):
            self.check()

    def test_recovered_archive_checks_original_time_notices_and_reads_same_bytes(self):
        self.target = 'https://archive.test/press'
        timestamp = '2026-11-01T12:00:00Z'
        with self.assertRaisesRegex(AssetError, 'original publication timestamp'):
            self.check(archive_base=self.target, published_at=timestamp)
        self.page += f'<time datetime="{timestamp}">1 November</time>'
        self.check(archive_base=self.target, published_at=timestamp)
        self.assertTrue(self.calls[-1].startswith(self.target))
