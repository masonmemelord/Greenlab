from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Sequence

import cv2 
import numpy as np
from matplotlib.path import Path as PolygonPath
from PIL import Image, ImageDraw 

#MatLab calibration: 200 micrometer scale bas measures 209px at 5x
BAR_PX = 209
BAR_UM = 200 
UM_PER_PX = BAR_UM / BAR_PX

IMAGE_EXTENSIONS = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"}

TIMEPOINT_LABELS = {
    "DIV7" : "DIV7",
    "DIV10" : "DIV10",
    "DIV14" : "DIV14",
    "DIV17" : "DIV17",
    "DIV21" : "DIV21",
    "repDIV3" : "replate DIV3",
    "repDIV5" : "replate DIV5",
    "repDIV7" : "replate DIV7",
    "repDIV9" : "replate DIV9",
}

CSV_COLUMNS =[
    "file",
    "area_px",
    "area_um2",
    "area_mm2",
    "equiv_diam_um",
    "note",
]

@dataclass
class ImageRecord:
    #One image and its saved manual-review result
    path: Path
    image: np.ndarray | None = field(default=None, rep=False)
    roi: list[tuple[float, float]] | None = None
    area_px: int | None = None
    area_um2: float | None = None
    area_mm2: float | None = None
    equiv_diam_um: float | None = None
    note: Literal["traced", "no colony"] | None = None

@dataclass
class TimepointData:
    #State that belongs only to one  experimental timepoint

    folder: Path | None = None
    um_per_px: float = UM_PER_PX
    images: list[ImageRecord] = field(default_factory=list)
    index: int = 0

def find_images(folder: str | Path) -> list[Path]:
    #Find every supported image; No magnification filename filter

    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"Image folder does not exist: {folder}")

    return sorted((
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ),
        key=lambda path: path.name.lower(),
    )

def load_display_image(image_path: str | Path) -> np.ndarray:
    """MATLAB equivalent of rgb2grey -> im2double -> imgaussfilt(..., 80) -> imadjust(gray/background)
        Returned image is only for easier manual tracing; measurements still sue polygon coords in the img pixel space
    """
    image = np.asarray(Image.open(image_path))

    if image.ndim == 3:
        grey = cv2.cvtColor(image[..., :3], cv2.COLOR_RGB2GRAY)
    else:
        grey = image

    if np.issubdtype(grey.dtype, np.integer):
        grey = grey.astype(np.float32) / np.iinfo(grey.dtype).max
    else:
        grey = grey.astype(np.float32)

    background = cv2.GaussianBlur(grey, (0,0), sigmaX=80)
    flattened = grey / np.maximum(background, 1e-3)

    return cv2.normalize(flattened, None, 0.0, 1.0, cv2.NORM_MINMAX)

def poly_to_mask(polygon_vertices: Sequence[Sequence[float]], image_shape: tuple[int, int],) -> np.ndarray:
    #Python equivalent of MATLAB 'createmask(roi)'
    vertices = np.asarray(polygon_vertices, dtype=float)

    if vertices.shape[0] < 3:
        raise ValueError("A colony outline needs at least three vertices.")

    height, width = image_shape[:2]
    x_grid, y_grid = np.meshgrid(np.arange(width), np.arange(height))
    points = np.column_stack((x_grid.ravel(), y_grid.ravel()))

    mask = PolygonPath(vertices).contains_points(points, radius=1e-9)
    return mask.reshape(height, width)

def measure_colony(polygon_vertices: Sequence[Sequence[float]], image_shape: tuple[int, int]
                   , um_per_px: float =UM_PER_PX,) -> dict[str, float]:
    #calculates the same measurements as 'manual_colony_tracer.m'.
    mask = poly_to_mask(polygon_vertices, image_shape)
    area_px = int(mask.sum())
    area_um2 = area_px * um_per_px**2

    return {
        "area_px": area_px,
        "area_um2": area_um2,
        "area_mm2": area_um2 / 1_000_000,
        "equiv_diam_um": 2 * math.sqrt(area_um2 / math.pi)
    }

class ManualColonyTacer:
    def __init__(self) -> None:
        self.timepoints = {
            key: TimepointData()
            for key in TIMEPOINT_LABELS
        }
        self.active_timepoint = "DIV7"

    @property
    def active_data(self) -> TimepointData:
        return self.timepoints[self.active_timepoint]

    @property
    def current_image(self) -> ImageRecord:
        data = self.active_data

        if not data.images:
            raise ValueError("Load an image before selecting an image.")
        return data.images[data.index]

    def select_timepoint(self, timepoint: str) -> None:
        if timepoint not in self.timepoints:
            raise ValueError(f"Unknown timepoint {self.timepoint}")

        self.active_timepoint = timepoint

    def load_folder(self, folder: str | Path) -> list[ImageRecord]:
        #Replace images only for the active timepoint.
        #Its calibration is intenetionally retained, matching MATLAB file.

        image_paths = find_images(folder)        
        if not image_paths:
            raise ValueError("No supported images found in folder.")

        data = self.active_data
        data.folder = Path(folder)
        data.images = [ImageRecord(path=path) for path in image_paths]
        data.index = 0

        return data.images

    def select_image(self, index: int) -> ImageRecord:
        if not 0 <= index < len(self.active_data.images):
            raise IndexError("Image index is out of range.")

        self.active_data.index = index
        return self.current_image

    def get_current_image_array(self) -> np.ndarray:
        #Load the active only when needed, then cache it in memory

        record = self.current_image

        if record.image is None:
            with Image.open(record.path) as source:
                record.image = np.asarray(source)
        return record.image

    def calibrate_active_timepoint(
            self,
            scale_bar_um: float,
            line_start: Sequence[float],
            line_end: Sequence[float],) -> float:
        #Translate MATLAB's Trace scale bar action
        #The frontend ahould send the two endpoints from its drawn line

        if scale_bar_um <= 0:
            raise ValueError("Scale-bar length must be positive.")
        if len(line_start) != 2 or len(line_end) != 2:
            raise ValueError("Scale-bar endpoints must each contain x and y values.")

        pixel_length = math.dist(line_start, line_end)

        if pixel_length <= 0:
            raise ValueError("Scale-bar pixel length must be positive.")

        data = self.active_data
        data.um_per_px = scale_bar_um / pixel_length

        #Recalculate all already saved traces for only this timepoint.
        for record in data.images:
            if record.note != "traced" or record.area_px is None:
                continue

            area_um2 = record.area_px * data.um_per_px**2
            record.area_um2 = area_um2
            record.area_mm2 = area_um2 / 1_000_000
            record.equiv_diam_um = 2 * math.sqrt(area_um2 / math.pi)

        return data.um_per_px

    def save_current_trace(
            self, polygon_vertices: Sequence[Sequence[float]],
            ) -> ImageRecord:
        #Save the current image's outline and calibrated measurements.

        image = self.get_current_image_array()
        result = measure_colony(
            polygon_vertices, image.shape[:2],
            self.active_data.um_per_px,
        )

        record = self.current_image
        record.roi = [
            (float(x), float(y))
            for x, y in polygon_vertices
        ]

        record.area_px = int(result["area_px"])
        record.area_um2 = result["area_um2"]
        record.area_mm2 = result["area_mm2"]
        record.equiv_diam_um = result["equiv_diam_um"]
        record.note = "traced"

        return record
    
    def mark_current_no_colony(self) -> ImageRecord:
        #Save a reviewd image as intentionally containing no colony

        record = self.current_image
        record.roi = None
        record.area_px = None
        record.area_um2 = None
        record.area_mm2 = None
        record.equiv_diam_um = None
        record.note = None

        return record

    def clear_current_result(self) -> ImageRecord:
        """Return the selected image to its unreviewed state."""

        record = self.current_image
        record.roi = None
        record.area_px = None
        record.area_um2 = None
        record.area_mm2 = None
        record.equiv_diam_um = None
        record.note = None

        return record


    def export_results(self, output_folder: str | Path) -> dict[str, Path]:
        #export the review-image CSV, reusable ROI coordinates, outline PNGs for tracked images.

        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        csv_path = output_folder / "colony_sizes.csv"
        roi_path = output_folder / "colony_rois.json"
        traced_root = output_folder / "traced_images"
        traced_root.mkdir(exist_ok=True)

        rows: list[dict[str, str | int | float | None]] = []
        roi_data: list[dict[str, object]] = []
        saved_images = 0

        for key, label in TIMEPOINT_LABELS.items():
            for record in self.timepoints[key].images:
                if record.note is None:
                    continue

                rows.append(
                    {
                        "Timepoint": label,
                        "file": record.path.name,
                        "area_px": record.area_px,
                        "area_um2": record.area_um2,
                        "area_mm2": record.area_mm2,
                        "equiv_diam_um": record.equiv_diam_um,
                        "note": record.note,
                    }
                )

                roi_data.append(
                    {
                        "Timepoint": label,
                        "file": record.path.name,
                        "position": record.roi,
                    }
                )

                if record.note == "traced" and record.roi:
                    timepoint_folder = traced_root / label.replace(" ", "_")
                    timepoint_folder.mkdir(exist_ok=True)

                    output_path = timepoint_folder / f"{record.path.stem}_traced.png"
                    self._save_traced_copy(record, output_path)
                    saved_images += 1

        if not rows:
            raise ValueError("No reviewed images are available to export.")

        with csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        with roi_path.open("w", encoding="utf-8") as file:
            json.dump(roi_data, file, indent=2)

        return {
            "csv": csv_path,
            "roi_data": roi_path,
            "traced_images": traced_root,
            "traced_image_count": saved_images,
        }

    @staticmethod
    def _save_traced_copy(record: ImageRecord, output_path: Path) -> None:
        """Save a red ROI outline over the original image as a PNG."""

        if not record.roi:
            return

        with Image.open(record.path) as source:
            overlay = source.convert("RGB")

        draw = ImageDraw.Draw(overlay)
        points = [tuple(point) for point in record.roi]

        # Re-add the first point so the colony outline closes.
        draw.line(
            points + [points[0]],
            fill=(255, 0, 0),
            width=4,
            joint="curve",
        )
        overlay.save(output_path, format="PNG")


