# PI requests: implementation and learning guide

## What changed and why

The image upload path had two separate problems. Browser image tags often cannot decode TIFFs, even when the file picker accepts them. Separately, Detect logged errors to the console and silently returned. An upload appearing successful did not mean inference succeeded.

All three web upload tools now support TIFF previews through `/api/image-preview`. Choose the page before uploading (UI pages start at 1; API indices start at 0). The backend preserves width and height, so displayed outlines still map to original pixels. Scalar 16-bit and floating-point images are scaled to 8-bit using the selected plane's minimum and maximum; this avoids Pillow clipping most microscope intensities to white. This is a display/model conversion, not raw intensity analysis. TIFF support is for Pillow-decodable planes, not automatic interpretation of OME channels, Z stacks, or scientific acquisition metadata. Choose the intended plane explicitly; calibration still requires verification against the microscope.

Detection now shows API/network errors and times out after three minutes. Zero detections is a valid result and is displayed as zero. Images are decoded by content instead of relying on an upload MIME type. Missing weights return an actionable 503. Loading weights is deferred until detection, and missing authentication database settings no longer prevent the image API from starting. Local development origins are allowed; use comma-separated `CORS_ORIGINS` for other deployments. `NEXT_PUBLIC_API_URL` must point to the FastAPI service and requires a frontend rebuild when changed.

YOLO's plot output is already BGR; removing an extra color conversion fixes swapped result colors. Test-time augmentation was disabled to avoid multiple inference passes and to support the colony segmentation path. This changes the detection baseline: record this version and rerun validation before comparing it with older runs.

## Train colony tracing from ROIs

The existing `best.pt` is a cell detection model. Bounding boxes do not supply colony boundaries. The new colony route requires separately trained segmentation weights. Polygon labels are the appropriate format for this approach: see [Ultralytics segmentation labels](https://docs.ultralytics.com/datasets/segment/) and [segmentation training](https://docs.ultralytics.com/tasks/segment/).

1. In Manual Colony Tracer, enter a reviewer ID, start the image timer, trace and Keep Trace (or No Colony), then download the training ROI JSON. Use a consistent, verified calibration. One saved colony decision per image/page is supported; use image crops if you need multiple separately labeled colonies. Saving again replaces that image's prior decision. Export before leaving the page.
2. Make an explicit JSON manifest. Each entry links one original image/page to its ROI export and split. Use absolute paths. Split by biological specimen, not just by image: keep related fields, timepoints, crops, and pages together to avoid leakage. The script rejects splitting pages from the same original file, but cannot infer specimen relationships across files.

```json
[
  {"image":"/absolute/train.tif", "rois":"/absolute/train_rois.json", "file":"train.tif", "page":1, "split":"train"},
  {"image":"/absolute/validation.tif", "rois":"/absolute/validation_rois.json", "file":"validation.tif", "page":1, "split":"val"},
  {"image":"/absolute/heldout.tif", "rois":"/absolute/test_rois.json", "file":"heldout.tif", "page":1, "split":"test"}
]
```

3. From the backend directory, prepare a new output folder:

```sh
.venv/bin/python scripts/prepare_colony_dataset.py /absolute/manifest.json /absolute/new_colony_dataset
```

4. Train a segmentation model, for example with the installed Ultralytics CLI. The base weights may need downloading. These are starting settings, not validated optimal settings:

```sh
.venv/bin/yolo segment train model=yolov8n-seg.pt data=/absolute/new_colony_dataset/data.yaml epochs=50 imgsz=640 batch=4 workers=0 project=ml/runs/segmentation name=colony_v1
```

5. Evaluate on the untouched test split. Only after reviewing results, install the trained run's `weights/best.pt` at `backend/ml/weights/segmentation/best.pt` and restart the backend. Auto circle then draws computer outlines in blue. Download computer ROI JSON for comparison. No segmentation weights were trained or installed as part of this implementation because annotated training data is still needed.

Pros: learns the lab's definition of a colony; supports outline overlap comparisons. Cons: needs representative, consistent annotations; can fail on new acquisition conditions. A saved ROI is a training example, not an immediate model update.

## Three-person study

Use three distinct anonymized reviewer IDs and the same held-out images/pages. Each reviewer should work independently, without viewing computer or other reviewer outlines. Agree in advance on colony inclusion rules, cell sampling rules, calibration, and timer boundaries. Export one session per reviewer. Browser state is temporary; CSV/JSON downloads are the records.

Colony timings start with Start image timer and end with Keep Trace or No Colony, including corrections. Every saved ROI retains reviewer, page, dimensions, calibration, geometry, and elapsed seconds. Computer timing currently excludes model loading, image decoding, upload, preview, and human review. Measure an additional end-to-end computer time if comparing practical workflow speed. Report inference and end-to-end time separately.

Compare computer contours with the three ROI exports, from the backend directory:

```sh
.venv/bin/python scripts/compare_colony_rois.py /absolute/computer_colony_rois.json /absolute/person1.json /absolute/person2.json /absolute/person3.json
```

The script reports IoU, Dice, area error against each reviewer, and timing. Both empty outlines receive overlap 1; report negative images separately so they do not inflate performance. Area error is undefined for an empty human reference. Multiple computer polygons are combined as a union: this measures overall colony coverage, not per-instance matching/count accuracy. Compare humans with one another as well and adjudicate disagreements before defining a reference. Three human measurements alone establish agreement, not objective accuracy.

For Cell Sizer, enter reviewer ID and start the timer after selecting each image. Each ellipse saves reviewer, page, geometry, and cumulative elapsed time. The final saved cell's elapsed time covers work through that save, not later review or zero-cell images. This initial instrumentation does not yet capture full completed-image sessions, automatic cell measurement timing, or compute matched-cell agreement. For a complete size study, preselect the same cell IDs/locations for all reviewers, define completion timing (including empty images) and pair those manual cells with automated measurements from `/api/cell-measure`. Count boxes from Detect are not cell size measurements. Do not sum cumulative cell times. Compare area and equivalent diameter errors on matched cells; report missed/extra cells separately.

## Verify and understand

Backend regression checks: from `backend`, run `.venv/bin/python -m unittest discover -s tests -v`. Frontend source type checking passes when excluding duplicate existing `.next/types` generated files; normal `tsc --noEmit` currently fails on those duplicate files. Changed-file ESLint has no errors, with existing native-image warnings.

Test yourself before collecting data:

- Why does accepting `.tiff` in a file input not guarantee that the browser can display it?
- Why must resizing a preview change the coordinate mapping, while intensity scaling does not?
- Why would putting different pages from the same specimen into train and test exaggerate model performance?
- What evidence would justify calling reviewer agreement accuracy?
- Why is a sum of cumulative per-cell times incorrect?

Try a small pilot with all three reviewers first. Check matching filenames/pages, ROI placement, calibration, timer boundaries, and exported columns before scaling the study.
