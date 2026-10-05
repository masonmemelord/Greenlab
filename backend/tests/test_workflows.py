import io
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from PIL import Image
from fastapi.testclient import TestClient
from app import main


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)
        buffer = io.BytesIO(); Image.new('RGB', (8, 6), 'white').save(buffer, format='TIFF')
        self.contents = buffer.getvalue()

    def test_preview_accepts_generic_mime_and_retains_size(self):
        result = self.client.post('/api/image-preview', files={'file': ('sample.tiff', self.contents, 'application/octet-stream')})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(Image.open(io.BytesIO(result.content)).size, (8, 6))

    def test_detection_zero_is_a_visible_success(self):
        import numpy as np
        result = SimpleNamespace(boxes=[], plot=lambda: np.zeros((6, 8, 3), dtype=np.uint8))
        with patch.object(main, 'get_detector', return_value=SimpleNamespace(predict=lambda *a, **k: result)):
            response = self.client.post('/api/detect', files={'files': ('sample.tiff', self.contents, 'application/octet-stream')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['cell_count'], 0)
        self.assertIn('elapsed_seconds', response.json()['results'][0])

    def test_inference_failure_is_actionable(self):
        def fail(*args, **kwargs): raise RuntimeError('test failure')
        with patch.object(main, 'get_detector', return_value=SimpleNamespace(predict=fail)):
            response = self.client.post('/api/detect', files={'files': ('sample.tiff', self.contents)})
        self.assertEqual(response.status_code, 500)
        self.assertIn('backend logs', response.json()['detail'])

    def test_missing_colony_weights(self):
        with patch.object(main, 'colony_detector', None), patch.object(main.Path, 'is_file', return_value=False):
            response = self.client.post('/api/colony-detect', files={'file': ('sample.tiff', self.contents)})
        self.assertEqual(response.status_code, 503)
        self.assertIn('ROI', response.json()['detail'])

if __name__ == '__main__': unittest.main()
