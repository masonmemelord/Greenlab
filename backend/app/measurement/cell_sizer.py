from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import re
import json

import numpy as np
import pandas as pd

from PIL import Image
from scipy import ndimage as ndi
from skimage import color, filters, measure, morphology, segmentation, util

IMAGE_EXTENSIONS = {".tif", ".tiff", ".png", ".jpeg", ".jpg", ".bmp"}

TIMEPOINTS = (
    "DIV7",
    "DIV10",
    "DIV14",
    "DIV17",
    "DIV21",
    "repDIV3",
    "repDIV5",
    "repDIV7",
    "repDIV9",
)

CELL_COLUMNS = [
    "CellID",
    "Source",
    "Centroid_X",
    "Centroid_Y",
    "Area_px",
    "Diam_px",
    "Major_px",
    "Minor_px",
    "Area_um2",
    "Diam_um",
]

def empty_cells() -> pd.DataFrame:
    #Equivalent of MATLAB emptyCellTable method.
    return pd.DataFrame(columns=CELL_COLUMNS)

def parse_magnification(filename: str) -> str:
    #Examples: sample_5x.TIFF -> '5x'; sample_10X.png -> '10x'
    match = re.search(r"(\d+)\s*[xX]", filename)

    if match is None:
        return "unknown"

    return f"{match.group(1)}x"

def find_images(folder: str | Path) -> list[Path]:
    #Find all supported image files, including .tif and .tiff
    folder = Path(folder)

    return sorted(
        (path 
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS),
        key=lambda path: path.name.lower(),
    )

def load_greyscale(image_path: str | Path) -> np.ndarray:
    #Loads an image with Pillow as a floating point greyscale val (0-1)
    #if RGB it converts to Greyscale
    image = np.asarray(Image.open(image_path))

    if image.ndim == 2:
        return util.img_as_float(image)
    return color.rgb2gray(image[..., :3]) #returns 2D pixel-brightness array for segmentation
    #this is so brightness can be reliable across the image as multiple RGB channels can be inconsistent

def make_detected_cells(properties: list, um_per_px: float | None) -> pd.DataFrame:
    #Convert scikit-image region properties into this app's cell table
    rows = []

    for cell_id, prop in enumerate(properties, start = 1): #for every region extract
        centroid_y, centroid_x = prop.centroid
        area_px = prop.area
        diameter_px = prop.equivalent_diameter

        rows.append({
            "CellID": cell_id,
            "Source": "auto",
            "Centroid_X": centroid_x, #center position X
            "Centroid_Y": centroid_y, #center position Y
            "Area_px": area_px, #area
            "Diam_px": diameter_px, #diameter in px
            "Major_px": prop.major_axis_length, #Major Axis length
            "Minor_px": prop.minor_axis_length, #Minor Axis length
            "Area_um2": area_px * um_per_px**2 if um_per_px else np.nan, #converts px area/diameter to µm^2 and µm
            "Diam_um": diameter_px * um_per_px if um_per_px else np.nan,
        })

    return pd.DataFrame(rows, columns=CELL_COLUMNS) #returns results as a Pandas table matching MATLAB format
        #helps make a unified table for auto and manually detected cells

@dataclass
class ImageRecord:
    path: Path
    magnification: str
    cells: pd.DataFrame = field(default_factory = empty_cells)

@dataclass
class TimepointData:
    calibrations: dict[str, float] = field(default_factory=dict)
    images: list[ImageRecord] = field(default_factory=list)
    index: int = 0

class CellSizer:
    #Python state model for CellSizerApp.m
    #One CellSizer instance retain seperae folders, calibrations and measurement tables for each experimental timepoint

    def __init__(self) -> None:
        self.timepoints = {
            name: TimepointData()
            for name in TIMEPOINTS
        }
        self.active_timepoint = "DIV7"
    
    @property
    def active_data(self) -> TimepointData:
        return self.timepoints[self.active_timepoint]

    @property
    def current_image(self) -> ImageRecord:
        data = self.active_data

        if not data.images:
            raise ValueError("Load an image folder before selecting an image")
        return data.images[data.index]
    
    def select_timepoint(self, timepoint: str) -> None:
        if timepoint not in self.timepoints:
            raise ValueError(f"Unknown timepoint: {timepoint}")

        self.active_timepoint = timepoint

    def load_folder(self, folder: str | Path) -> list[ImageRecord]:
        #Equivalent of MATLAB onLoadFolder.
        #Loads a replacement folder clears prior cells and calibrations only for the currently active timepoint

        image_paths = find_images(folder)

        if not image_paths:
            raise ValueError("No support image files were found in this folder.")

        self.timepoints[self.active_timepoint] = TimepointData(
            images=[
                ImageRecord(
                    path=path,
                    magnification=parse_magnification(path.name)
                )
                for path in image_paths
            ]
        )

        return self.active_data.images

    def select_image(self, index: int) -> ImageRecord:
        data = self.active_data

        if not 0 <= index < len(data.images):
            raise IndexError("Image index is out of range.")

        data.index = index
        return self.current_image

    def calibrate_current_magnification(self, scale_bar_um: float, pixel_length: float) -> float:
        #Saves µm/px for the current images' magnification.
        #pixel_length will later come from a line the user traces on screen.

        if scale_bar_um <= 0 or pixel_length <= 0:
            raise ValueError("Scale-bar length and pixel length must be positive.")

        um_per_px = scale_bar_um / pixel_length
        magnification = self.current_image.magnification
        self.active_data.calibrations[magnification] = um_per_px

        #MATLAB recomputes units for existing measuremnts of this magnification
        for image in self.active_data.images:
            if image.magnification != magnification or image.cells.empty:
                continue

            image.cells["Area_um2"] = image.cells["Area_px"] * um_per_px**2
            image.cells["Diam_um"] = image.cells["Diam_px"] * um_per_px

        return um_per_px

    def current_calibration(self) -> float | None:
        return self.active_data.calibrations.get(
            self.current_image.magnification
        )

    def current_image_dimensions(self) -> tuple[int, int]:
        #Returns the selected image size in width, height format
        with Image.open(self.current_image.path) as image:
            return image.size

    @staticmethod
    def grid_cell_of(
        x: float,
        y: float,
        image_width: int, image_height: int,
        grid_rows: int,
        grid_cols: int,
    ) -> tuple[int, int]: #Converts cell center into a grid in tuple format
        if grid_rows < 1 or grid_cols < 1: #edge cases
            raise ValueError("Grid rows and columns must both be at least 1.")

        col = min(grid_cols - 1, max(0, int(x / image_width * grid_cols))) #range for columns
        row = min(grid_rows - 1, max(0, int(y / image_height * grid_rows))) #range for rows

        return row, col

    def occupied_grid_squares(
            self,
            grid_rows: int,
            grid_cols: int
    ) -> np.ndarray: #Returns a T/F grid. Only manually circled cells occupy a square.
        occupied = np.zeros((grid_rows, grid_cols), dtype=bool)
        image_width, image_height = self.current_image_dimensions()
        cells = self.current_image.cells

        manual_cells = cells[cells["Source"] == "manual"]

        for _, cell in manual_cells.iterrows():
            row, col = self.grid_cell_of(
                cell["Centroid_X"], cell["Centroid_Y"],
                image_width, 
                image_height,
                grid_rows, 
                grid_cols,
            )
            occupied[row, col] = True

        return occupied

    def add_manual_cell(
            self,
            center_x: float, 
            center_y: float,
            semi_axis_x: float, 
            semi_axis_y: float,
            *,
            grid_rows: int | None = None, 
            grid_cols: int | None = None,
            replace_existing: bool = False,
    )   -> pd.DataFrame: #Save one manually drawn ellipse. Optional grid enforcement, primarily for manual tracing
        
        if semi_axis_x <= 0 or semi_axis_y <= 0:
            raise ValueError("Both ellipse semi-axes must be positive.")

        record = self.current_image
        cells = record.cells.copy()

        if grid_rows is not None and grid_cols is not None:
            image_width, image_height = self.current_image_dimensions()
            row, col = self.grid_cell_of(
                center_x, center_y,
                image_width, 
                image_height,
                grid_rows,
                grid_cols,
            )

            duplicate_indexes = []

            for index, cell in cells[cells["Source"] == "manual"].iterrows():
                cell_row, cell_col = self.grid_cell_of(
                    cell["Centroid_X"],
                    cell["Centroid_Y"],
                    image_width,
                    image_height,
                    grid_rows,
                    grid_cols,
                )
                if cell_row == row and cell_col == col:
                    duplicate_indexes.append(index)

            if duplicate_indexes and not replace_existing:
                raise ValueError(
                    f"Grid square row {row + 1}, column {col + 1}"
                    "already has a manually selected cell."
                )

            if duplicate_indexes:
                cells = cells.drop(index=duplicate_indexes)

        area_px = np.pi * semi_axis_x * semi_axis_y
        diameter_px = 2 * np.sqrt(semi_axis_x * semi_axis_y)
        major_px = 2 * max(semi_axis_x, semi_axis_y)
        minor_px = 2 * min(semi_axis_x, semi_axis_y)
        um_per_px = self.current_calibration()

        manual_row = pd.DataFrame(
            [{
                "CellID": 0,
                "Source": "manual",
                "Centroid_X": center_x,
                "Centroid_Y": center_y,
                "Area_px": area_px,
                "Diam_px": diameter_px,
                "Major_px": major_px,
                "Minor_px": minor_px,
                "Area_um2": (
                    area_px * um_per_px ^ 2
                    if um_per_px is not None else np.nan
                    ),
                    "Diam_um": (
                        diameter_px * um_per_px
                        if um_per_px is not None else np.nan
                    ),
            }],
            columns=CELL_COLUMNS,
        )

        record.cells = pd.concat(
            [cells, manual_row],
            ignore_index=True,
        )
        record.cells["CellID"] = range(1, len(record.cells) + 1)

        return record.cells

    def remove_nearest_cell(
        self,
        x: float,
        y: float,
    ) -> pd.DataFrame: #Remove whichever saved cell is nearest to the supplied x,y coord

        record = self.current_image
        if record.cells.empty:
            return record.cells

        distances = np.hypot(
            record.cells["Centroid_X"] - x,
            record.cells["Centroid_Y"] - y,
        )
        nearest_index = distances.idxmin()

        record.cells = record.cells.drop(index=nearest_index).reset_index(drop=True)
        record.cells["CellID"] = range(1, len(record.cells) + 1)

        return record.cells

    def clear_current_cells(self) -> pd.DataFrame:
        self.current_image.cells = empty_cells()
        return self.current_image.cells


    def detect_current(self, *, sensitivity: float = 0.5, #loads greyscale ImageRecord
                       cells_darker_than_bg: bool = False,
                       min_diameter_um: float = 3,
                       max_diameter_um: float = 100,
                       split_touching_cells: bool = True,
                       h_min: float = 2,
                       ) -> pd.DataFrame:
        #Python equivalent of MATLAB's detectOne for selected image
        #h_min remains measured in px, matching MATLAB app.

        if not 0 <= sensitivity <= 1: 
            raise ValueError("Sensitivity must be between 0 and 1.")

        if min_diameter_um <= 0 or max_diameter_um <= min_diameter_um:
            raise ValueError("Use a positive minimum diameter less than the maximum")

        img_record = self.current_image
        grey = load_greyscale(img_record.path)

        if cells_darker_than_bg: #if cells are darker than background
            grey = 1.0 - grey 

        #Appx MATLAB's adaptthresh(..., sensitivity) behavior.
        #Higher sensitivity lowrs threshold and finds more fg.
        offset = (0.5 - sensitivity) * 0.4 
        local_threshold = filters.threshold_local(
            grey, block_size=51, method="gaussian", offset=offset
        )

        binary = grey > local_threshold #pixel belongs to a cell
        binary = ndi.binary_fill_holes(binary) 

        um_per_px = self.current_calibration()

        if um_per_px is None:
            min_diameter_px = min_diameter_um
            max_diameter_px = max_diameter_um
        else:
            min_diameter_px = min_diameter_um / um_per_px
            max_diameter_px = max_diameter_um / um_per_px

        mininum_area_px = max(1, int(np.ceil(np.pi * (min_diameter_px / 2) ** 2)),
        )

        binary = morphology.remove_small_objects(
            binary.astype(bool), #Converts threshold into a Boolean mask
            min_size = mininum_area_px,
        )

        if split_touching_cells and binary.any(): #splits touching cells 
            distance = ndi.distance_transform_edt(binary)

            if h_min > 0:
                peaks = morphology.h_maxima(distance, h_min)
            else:
                peaks = morphology.local_maxima(distance)

            markers = measure.label(peaks)

            if markers.max() > 0: #measures every region and removes everything outside diameter
                labels = segmentation.watershed(
                    -distance,
                    markers=markers,
                    mask = binary,
                )
            else:
                labels = measure.label(binary)
        else:
            labels = measure.label(binary)

        properties = measure.regionprops(labels)

        valid_properties = [prop for prop in properties 
                            if min_diameter_px <= prop.equivalent_diameter <= max_diameter_px]

        img_record.cells = make_detected_cells(
            valid_properties,
            um_per_px,
        )
        
        return img_record.cells #stores final table
    
def measure_image(image_path: str | Path, *, 
                          sensitivity: float = 0.5, 
                          cell_darker_than_bg: bool = False,
                          min_diameter_um: float = 3,
                          max_diameter_um: float = 100,
                          split_touching_cells: bool = True,
                          h_min: float = 2,
                          um_per_px: float | None = None,) -> pd.DataFrame:
        """
        Stateless wrapper for FastAPI.
    
        Each request gets its own CellSizer, prevents data from persisting across requests
        """
    
        path = Path(image_path)
        sizer = CellSizer()
    
        image = ImageRecord(path = path, magnification=parse_magnification(path.name))
        sizer.active_data.images = [image]
    
        if um_per_px is not None:
            if um_per_px <= 0:
                raise ValueError("um_per_px must be positive.")
    
            sizer.active_data.calibrations[image.magnification] = um_per_px
    
        return sizer.detect_current(
                sensitivity=sensitivity,
                cells_darker_than_bg=cell_darker_than_bg,
                min_diameter_um=min_diameter_um,
                max_diameter_um=max_diameter_um,
                split_touching_cells=split_touching_cells,
                h_min=h_min,
        )

    