'use client';

import {
  type PointerEvent as ReactPointerEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

type Point = { x: number; y: number };

type Preview = {
  id: string;
  filename: string;
  timepoint: string;
  url: string;
};

type ManualCell = {
  id: string;
  imageId: string;
  timepoint: string;
  file: string;
  source: 'manual';
  centroidX: number;
  centroidY: number;
  semiAxisX: number;
  semiAxisY: number;
  areaPx: number;
  diameterPx: number;
  majorPx: number;
  minorPx: number;
  areaUm2: number;
  diameterUm: number;
};

type Drag = {
  start: Point;
  current: Point;
};

const TIMEPOINTS = [
  ['DIV7', 'DIV7'],
  ['DIV10', 'DIV10'],
  ['DIV14', 'DIV14'],
  ['DIV17', 'DIV17'],
  ['DIV21', 'DIV21'],
  ['repDIV3', 'replate DIV3'],
  ['repDIV5', 'replate DIV5'],
  ['repDIV7', 'replate DIV7'],
  ['repDIV9', 'replate DIV9'],
] as const;

const DEFAULT_UM_PER_PX = 200 / 209;

function csvValue(value: string | number) {
  const text = String(value);
  // A filename can be user-controlled; prefix spreadsheet formulas so opening the CSV cannot execute one.
  const safeText = /^[=+\-@]/.test(text) ? `'${text}` : text;
  return `"${safeText.replace(/"/g, '""')}"`;
}

function gridKeyForPoint(
  point: Point,
  imageWidth: number,
  imageHeight: number,
  rows: number,
  cols: number,
) {
  const row = Math.min(rows - 1, Math.max(0, Math.floor((point.y / imageHeight) * rows)));
  const col = Math.min(cols - 1, Math.max(0, Math.floor((point.x / imageWidth) * cols)));
  return `${row}:${col}`;
}

export default function CellSizerPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const objectUrlsRef = useRef<string[]>([]);

  const [activeTimepoint, setActiveTimepoint] = useState('DIV7');
  const [previews, setPreviews] = useState<Preview[]>([]);
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);
  const [cells, setCells] = useState<ManualCell[]>([]);
  const [calibrations, setCalibrations] = useState<Record<string, number>>(
    () => Object.fromEntries(TIMEPOINTS.map(([key]) => [key, DEFAULT_UM_PER_PX])),
  );
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [gridRows, setGridRows] = useState(4);
  const [gridCols, setGridCols] = useState(4);
  const [showGrid, setShowGrid] = useState(true);
  const [limitOnePerSquare, setLimitOnePerSquare] = useState(true);
  const [replaceOccupiedSquare, setReplaceOccupiedSquare] = useState(false);
  const [drag, setDrag] = useState<Drag | null>(null);
  const [removeMode, setRemoveMode] = useState(false);
  const [previewError, setPreviewError] = useState(false);
  const [message, setMessage] = useState('Upload images for a timepoint, then drag an ellipse around each manually selected cell.');

  // Object URLs are only local image previews; release them when this browser-only page unmounts.
  useEffect(() => {
    const objectUrls = objectUrlsRef.current;
    return () => objectUrls.forEach((url) => URL.revokeObjectURL(url));
  }, []);

  const activeImages = useMemo(
    () => previews.filter((preview) => preview.timepoint === activeTimepoint),
    [activeTimepoint, previews],
  );
  const selectedPreview = activeImages.find((preview) => preview.id === selectedImageId) ?? null;
  const currentCells = useMemo(
    () => cells.filter((cell) => cell.imageId === selectedImageId),
    [cells, selectedImageId],
  );
  const umPerPx = calibrations[activeTimepoint] ?? DEFAULT_UM_PER_PX;

  function resetCanvas() {
    setDrag(null);
    setRemoveMode(false);
    setImageSize({ width: 0, height: 0 });
    setPreviewError(false);
  }

  function selectTimepoint(timepoint: string) {
    setActiveTimepoint(timepoint);
    const firstImage = previews.find((preview) => preview.timepoint === timepoint);
    setSelectedImageId(firstImage?.id ?? null);
    resetCanvas();
  }

  function handleFiles(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (files.length === 0) return;

    const newPreviews = files.map((file) => {
      const url = URL.createObjectURL(file);
      objectUrlsRef.current.push(url);

      return {
        id: crypto.randomUUID(),
        filename: file.name,
        timepoint: activeTimepoint,
        url,
      };
    });

    setPreviews((current) => [...current, ...newPreviews]);
    setSelectedImageId(newPreviews[0].id);
    resetCanvas();
    setMessage(`${newPreviews.length} image(s) added to ${activeTimepoint}.`);

    // Allow selecting the same file again after clearing or correcting a review.
    event.target.value = '';
  }

  function selectImage(imageId: string) {
    setSelectedImageId(imageId);
    resetCanvas();
  }

  // All ellipse positions are converted to natural image pixels before being saved or exported.
  function pointerToImagePoint(event: ReactPointerEvent<SVGSVGElement>): Point | null {
    if (!imageSize.width || !imageSize.height) return null;

    const bounds = event.currentTarget.getBoundingClientRect();

    return {
      x: ((event.clientX - bounds.left) / bounds.width) * imageSize.width,
      y: ((event.clientY - bounds.top) / bounds.height) * imageSize.height,
    };
  }

  const occupiedSquares = useMemo(() => {
    if (!imageSize.width || !imageSize.height) return new Set<string>();

    return new Set(currentCells.map((cell) => gridKeyForPoint(
      { x: cell.centroidX, y: cell.centroidY },
      imageSize.width,
      imageSize.height,
      gridRows,
      gridCols,
    )));
  }, [currentCells, gridRows, gridCols, imageSize]);

  function removeNearestCell(point: Point) {
    if (currentCells.length === 0) {
      setMessage('There are no saved manual cells on this image to remove.');
      return;
    }

    const nearest = currentCells.reduce((closest, cell) => {
      const distance = Math.hypot(cell.centroidX - point.x, cell.centroidY - point.y);
      return distance < closest.distance ? { cell, distance } : closest;
    }, { cell: currentCells[0], distance: Number.POSITIVE_INFINITY });

    setCells((current) => current.filter((cell) => cell.id !== nearest.cell.id));
    setRemoveMode(false);
    setMessage(`Removed the manual cell nearest to your click in ${selectedPreview?.filename}.`);
  }

  function finishEllipse(nextDrag: Drag) {
    if (!selectedPreview) return;

    const semiAxisX = Math.abs(nextDrag.current.x - nextDrag.start.x) / 2;
    const semiAxisY = Math.abs(nextDrag.current.y - nextDrag.start.y) / 2;

    if (semiAxisX < 2 || semiAxisY < 2) {
      setMessage('Draw a larger ellipse around the cell before releasing.');
      return;
    }

    const center = {
      x: (nextDrag.start.x + nextDrag.current.x) / 2,
      y: (nextDrag.start.y + nextDrag.current.y) / 2,
    };
    const square = gridKeyForPoint(
      center,
      imageSize.width,
      imageSize.height,
      gridRows,
      gridCols,
    );
    const occupied = occupiedSquares.has(square);

    if (showGrid && limitOnePerSquare && occupied && !replaceOccupiedSquare) {
      setMessage('That grid square already has a manual cell. Enable replacement or choose another square.');
      return;
    }

    const areaPx = Math.PI * semiAxisX * semiAxisY;
    const diameterPx = 2 * Math.sqrt(semiAxisX * semiAxisY);
    const manualCell: ManualCell = {
      id: crypto.randomUUID(),
      imageId: selectedPreview.id,
      timepoint: activeTimepoint,
      file: selectedPreview.filename,
      source: 'manual',
      centroidX: center.x,
      centroidY: center.y,
      semiAxisX,
      semiAxisY,
      areaPx,
      diameterPx,
      majorPx: 2 * Math.max(semiAxisX, semiAxisY),
      minorPx: 2 * Math.min(semiAxisX, semiAxisY),
      areaUm2: areaPx * umPerPx ** 2,
      diameterUm: diameterPx * umPerPx,
    };

    setCells((current) => {
      const withoutReplacedCell = !showGrid || !limitOnePerSquare || !occupied || !replaceOccupiedSquare
        ? current
        : current.filter((cell) => cell.imageId !== selectedPreview.id || gridKeyForPoint(
          { x: cell.centroidX, y: cell.centroidY },
          imageSize.width,
          imageSize.height,
          gridRows,
          gridCols,
        ) !== square);

      return [...withoutReplacedCell, manualCell];
    });
    setMessage(`Saved manual cell ${currentCells.length + 1} on ${selectedPreview.filename}.`);
  }

  function updateCalibration(value: number) {
    if (!Number.isFinite(value) || value <= 0) return;

    setCalibrations((current) => ({ ...current, [activeTimepoint]: value }));

    // Match MATLAB: changing a timepoint's calibration recomputes every saved cell in that timepoint.
    setCells((current) => current.map((cell) => {
      if (cell.timepoint !== activeTimepoint) return cell;

      return {
        ...cell,
        areaUm2: cell.areaPx * value ** 2,
        diameterUm: cell.diameterPx * value,
      };
    }));
  }

  function clearCurrentImage() {
    if (!selectedPreview) return;

    setCells((current) => current.filter((cell) => cell.imageId !== selectedPreview.id));
    setMessage(`Cleared manual cells from ${selectedPreview.filename}.`);
  }

  function downloadCsv() {
    if (cells.length === 0) {
      setMessage('Save at least one manual cell before exporting a CSV.');
      return;
    }

    const headers = [
      'Timepoint', 'file', 'Source', 'Centroid_X', 'Centroid_Y',
      'Area_px', 'Diam_px', 'Major_px', 'Minor_px', 'Area_um2', 'Diam_um',
    ];
    const rows = cells.map((cell) => [
      cell.timepoint, cell.file, cell.source,
      cell.centroidX.toFixed(2), cell.centroidY.toFixed(2),
      cell.areaPx.toFixed(2), cell.diameterPx.toFixed(2),
      cell.majorPx.toFixed(2), cell.minorPx.toFixed(2),
      cell.areaUm2.toFixed(2), cell.diameterUm.toFixed(2),
    ].map(csvValue).join(','));

    const blob = new Blob([[headers.join(','), ...rows].join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'manual_cell_sizes.csv';
    link.click();
    URL.revokeObjectURL(url);
  }

  const pendingEllipse = drag && {
    cx: (drag.start.x + drag.current.x) / 2,
    cy: (drag.start.y + drag.current.y) / 2,
    rx: Math.abs(drag.current.x - drag.start.x) / 2,
    ry: Math.abs(drag.current.y - drag.start.y) / 2,
  };

  return (
    <main className="gl-page">
      <div className="gl-container">
        <nav className="gl-nav">
          <h1 className="gl-nav__title">Manual Cell Sizer</h1>
          <div className="gl-nav__links">
            <a href="/dashboard" className="gl-nav__link">Back to Dashboard</a>
            <a href="/manual_tracer" className="gl-nav__link">Colony Tracer</a>
          </div>
        </nav>

        <section className="gl-card">
          <h2 className="gl-manual__title">Manual cell sampling</h2>
          <p className="gl-manual__hint">
            This is a browser-only manual workflow. It does not run auto-detection or send images to the database.
          </p>

          <div className="gl-sizer__controls">
            <label>
              Timepoint
              <select className="gl-input" value={activeTimepoint} onChange={(event) => selectTimepoint(event.target.value)}>
                {TIMEPOINTS.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
              </select>
            </label>

            <label>
              Calibration (µm / pixel)
              <input
                className="gl-input"
                type="number"
                min="0.0001"
                step="0.0001"
                value={umPerPx}
                onChange={(event) => updateCalibration(Number(event.target.value))}
              />
            </label>

            <label>
              Grid rows
              <input className="gl-input" type="number" min="1" value={gridRows} onChange={(event) => setGridRows(Math.max(1, Number(event.target.value)))} />
            </label>

            <label>
              Grid columns
              <input className="gl-input" type="number" min="1" value={gridCols} onChange={(event) => setGridCols(Math.max(1, Number(event.target.value)))} />
            </label>
          </div>

          <div className="gl-sizer__checks">
            <label><input type="checkbox" checked={showGrid} onChange={(event) => setShowGrid(event.target.checked)} /> Show sampling grid</label>
            <label><input type="checkbox" checked={limitOnePerSquare} onChange={(event) => setLimitOnePerSquare(event.target.checked)} /> Limit to one manual cell per square</label>
            <label><input type="checkbox" checked={replaceOccupiedSquare} onChange={(event) => setReplaceOccupiedSquare(event.target.checked)} /> Replace occupied square</label>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".png,.jpg,.jpeg,.tif,.tiff,.bmp"
            multiple
            onChange={handleFiles}
            style={{ display: 'none' }}
          />
          <button className="gl-btn gl-btn--primary" onClick={() => fileInputRef.current?.click()}>
            Add Images for {activeTimepoint}
          </button>
        </section>

        {activeImages.length > 0 && (
          <section className="gl-card">
            <div className="gl-sizer__toolbar">
              <label className="gl-sizer__image-select">
                Image
                <select className="gl-input" value={selectedImageId ?? ''} onChange={(event) => selectImage(event.target.value)}>
                  {activeImages.map((preview, index) => <option key={preview.id} value={preview.id}>{index + 1}. {preview.filename}</option>)}
                </select>
              </label>
              <span className="gl-sizer__count">Manual cells on this image: {currentCells.length}</span>
            </div>

            {previewError ? (
              <p className="gl-msg gl-msg--error">This browser cannot preview the selected TIFF. Use PNG/JPG for browser-based manual cell sizing.</p>
            ) : selectedPreview && (
              <div className="gl-sizer__surface">
                {/* A native image preserves the uploaded file's exact natural dimensions for ellipse measurements. */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={selectedPreview.url}
                  className="gl-sizer__image"
                  alt={`Manual cell sizing canvas for ${selectedPreview.filename}`}
                  onLoad={(event) => setImageSize({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })}
                  onError={() => setPreviewError(true)}
                />

                {imageSize.width > 0 && (
                  <svg
                    className={`gl-sizer__overlay${removeMode ? ' gl-sizer__overlay--remove' : ''}`}
                    viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
                    onPointerDown={(event) => {
                      event.preventDefault();
                      const point = pointerToImagePoint(event);
                      if (!point) return;

                      if (removeMode) {
                        removeNearestCell(point);
                        return;
                      }

                      event.currentTarget.setPointerCapture(event.pointerId);
                      setDrag({ start: point, current: point });
                    }}
                    onPointerMove={(event) => {
                      if (!drag) return;
                      const point = pointerToImagePoint(event);
                      if (point) setDrag((current) => current ? { ...current, current: point } : null);
                    }}
                    onPointerUp={(event) => {
                      if (!drag) return;
                      const point = pointerToImagePoint(event);
                      event.currentTarget.releasePointerCapture(event.pointerId);
                      const completedDrag = { ...drag, current: point ?? drag.current };
                      setDrag(null);
                      finishEllipse(completedDrag);
                    }}
                    onPointerCancel={() => setDrag(null)}
                  >
                    {showGrid && Array.from({ length: gridRows * gridCols }, (_, index) => {
                      const row = Math.floor(index / gridCols);
                      const col = index % gridCols;
                      const isOccupied = occupiedSquares.has(`${row}:${col}`);

                      return <rect
                        key={`${row}:${col}`}
                        x={(col * imageSize.width) / gridCols}
                        y={(row * imageSize.height) / gridRows}
                        width={imageSize.width / gridCols}
                        height={imageSize.height / gridRows}
                        className={isOccupied ? 'gl-sizer__grid-cell gl-sizer__grid-cell--occupied' : 'gl-sizer__grid-cell'}
                      />;
                    })}

                    {currentCells.map((cell) => <ellipse
                      key={cell.id}
                      cx={cell.centroidX}
                      cy={cell.centroidY}
                      rx={cell.semiAxisX}
                      ry={cell.semiAxisY}
                      className="gl-sizer__cell"
                    />)}

                    {pendingEllipse && <ellipse {...pendingEllipse} className="gl-sizer__cell gl-sizer__cell--pending" />}
                  </svg>
                )}
              </div>
            )}

            <div className="gl-manual__actions">
              <button className="gl-btn gl-btn--primary" onClick={() => { setRemoveMode(false); setMessage('Drag over a cell to save its ellipse.'); }}>
                Draw Cell
              </button>
              <button className="gl-btn gl-btn--csv" onClick={() => { setRemoveMode((current) => !current); setMessage('Click the saved cell nearest the one you want to remove.'); }}>
                {removeMode ? 'Cancel Remove' : 'Remove Cell'}
              </button>
              <button className="gl-btn gl-btn--csv" onClick={clearCurrentImage}>Clear This Image</button>
              <button className="gl-btn gl-btn--csv" onClick={downloadCsv}>Download CSV ({cells.length})</button>
            </div>
          </section>
        )}

        <p className="gl-result-msg">{message}</p>
      </div>
    </main>
  );
}
