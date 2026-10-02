"""PDF 文本覆盖与扫描件误报的定向回归；仅使用合成文件。"""
import io
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' if (ROOT / 'scripts').is_dir() else ROOT))
from PIL import Image
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
import contract_sensitive_detector as detector
import contract_app_server as app
import contract_app_ui as ui
from contract_redactor import redact_file


def make_pdf(path, pages):
    c = Canvas(str(path), pagesize=(300, 300))
    for kind in pages:
        if kind == 'image':
            c.drawImage(ImageReader(Image.new('RGB', (240, 240), '#eee')), 30, 30, 240, 240)
        elif kind == 'text':
            c.drawString(30, 200, 'ordinary public text')
        elif kind == 'short':
            c.drawString(30, 200, 'hello')
        c.showPage()
    c.save()


class PDFTextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_scanned_pdf_is_not_a_no_sensitive_result(self):
        path = self.root / 'scan.pdf'; make_pdf(path, ['image'])
        doc = detector.extract_pdf(str(path))
        self.assertEqual(doc.unreadable_pages, [1])
        with self.assertRaisesRegex(detector.PdfTextLayerError, '不代表文件没有敏感信息'):
            app._run_detector(str(path))

    def test_mixed_pdf_cannot_silently_skip_image_page(self):
        path = self.root / 'mixed.pdf'; make_pdf(path, ['text', 'image'])
        doc = detector.extract_pdf(str(path))
        self.assertTrue(doc.text)
        self.assertEqual(doc.unreadable_pages, [2])
        with self.assertRaisesRegex(detector.PdfTextLayerError, '第 2 页'):
            detector.require_pdf_text(doc)

    def test_intentionally_blank_page_does_not_block_readable_pdf(self):
        path = self.root / 'blank.pdf'; make_pdf(path, ['text', 'blank'])
        run = app._run_detector(str(path))
        self.assertEqual(run['doc'].unreadable_pages, [])
        self.assertEqual(run['report']['summary']['occurrences'], 0)

    def test_short_readable_pdf_remains_supported(self):
        path = self.root / 'short.pdf'; make_pdf(path, ['short'])
        run = app._run_detector(str(path))
        self.assertEqual(run['doc'].text, 'hello')
        page = ui.build_review_page('demo', {'filename': 'short.pdf', 'report': run['report'],
                      'review_payload': app._build_review_payload(run['report'], run['doc'].blocks)}).decode()
        self.assertIn('解析提示', page)
        self.assertNotIn('文档保持原样即可', page)

    def test_direct_export_of_unreadable_pdf_is_blocked(self):
        path = self.root / 'scan.pdf'; make_pdf(path, ['image'])
        out = self.root / 'out.pdf'
        with self.assertRaises(detector.PdfTextLayerError):
            redact_file(str(path), types=['PHONE'], out_path=str(out))
        self.assertFalse(out.exists())

    def test_http_upload_rejects_scan_and_removes_failed_upload(self):
        server = app.start_app_server('127.0.0.1', 0, str(self.root / 'sessions'))
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        try:
            for kinds in (['image'], ['text', 'image']):
                path = self.root / 'scan.pdf'; make_pdf(path, kinds)
                boundary = 'pdftexttest'
                data = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="scan.pdf"\r\n'
                        'Content-Type: application/pdf\r\n\r\n').encode() + path.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
                req = urllib.request.Request(f'http://127.0.0.1:{server.server_port}/api/upload', data=data,
                         headers={'Content-Type': 'multipart/form-data; boundary='+boundary})
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(req)
                self.assertEqual(error.exception.code, 400)
                result = json.loads(error.exception.read())
                self.assertEqual(result['code'], 'PDF_TEXT_UNREADABLE')
                self.assertFalse(list((self.root / 'sessions').rglob('scan.pdf')))
        finally:
            server.shutdown(); server.server_close(); worker.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
