import io
import unittest
import numpy as np
from PIL import Image
from app.imaging import read_plane


class ImageTests(unittest.TestCase):
    def test_16_bit_tiff_keeps_dimensions_and_contrast(self):
        source = Image.fromarray(np.array([[1000, 2000], [3000, 4000]], dtype=np.uint16))
        buffer = io.BytesIO(); source.save(buffer, format='TIFF')
        image, pages = read_plane(buffer.getvalue())
        self.assertEqual(image.size, (2, 2))
        self.assertEqual(pages, 1)
        self.assertEqual(list(image.get_flattened_data()), [(0, 0, 0), (85, 85, 85), (170, 170, 170), (255, 255, 255)])

    def test_selected_page_and_out_of_range(self):
        buffer = io.BytesIO()
        Image.new('RGB', (5, 3), 'red').save(buffer, format='TIFF', save_all=True, append_images=[Image.new('RGB', (5, 3), 'blue')])
        image, pages = read_plane(buffer.getvalue(), 1)
        self.assertEqual(pages, 2)
        self.assertEqual(image.getpixel((0, 0)), (0, 0, 255))
        with self.assertRaises(ValueError): read_plane(buffer.getvalue(), 2)

    def test_invalid_data(self):
        with self.assertRaises(OSError): read_plane(b'not an image')

if __name__ == '__main__': unittest.main()
