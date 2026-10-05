"""Decode a selected image plane without changing its pixel coordinates."""
import io
import numpy as np
from PIL import Image


def read_plane(contents: bytes, page: int = 0) -> tuple[Image.Image, int]:
    with Image.open(io.BytesIO(contents)) as source:
        pages = getattr(source, 'n_frames', 1)
        if page < 0 or page >= pages:
            raise ValueError(f'Page {page + 1} does not exist; image has {pages} page(s).')
        source.seek(page)
        # Pillow's direct RGB conversion clips 16-bit microscopy data at 255.
        # Scale the selected plane for display/model input; never resize it.
        if source.mode.startswith('I') or source.mode == 'F':
            values = np.asarray(source, dtype=np.float64)
            if not np.isfinite(values).all():
                raise ValueError('Image contains non-finite intensities.')
            low, high = values.min(), values.max()
            scaled = (values - low) * (255 / (high - low)) if high > low else np.zeros_like(values)
            image = Image.fromarray(scaled.astype(np.uint8)).convert('RGB')
        else:
            image = source.convert('RGB')
        return image, pages
