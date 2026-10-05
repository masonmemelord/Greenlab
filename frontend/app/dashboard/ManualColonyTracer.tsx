'use client';

import {
  type PointerEvent as ReactPointerEvent,
  useMemo,
  useRef,
  useState,
} from 'react';

import { apiUrl, apiError } from '@/lib/images';

type Point = { x: number; y: number };

type Preview = {
  filename: string;
  url: string;
  file: File;
  page: number;
};

type Measurement = {
  id: number;
  reviewer: string;
  elapsed_seconds: number;
  width: number;
  height: number;
  page: number;
  um_per_px: number;
  points: Point[];
  file: string;
  area_px: number | null;
  area_um2: number | null;
  area_mm2: number | null;
  equiv_diam_um: number | null;
  note: 'traced' | 'no colony';
};

type ManualColonyTracerProps = {
  previews: Preview[];
};

// Matches the default calibration from manual_colony_tracer.m (200 µm / 209 px).
const DEFAULT_UM_PER_PX = 200 / 209;

function polygonArea(points: Point[]) {
  if (points.length < 3) return 0;

  const doubleArea = points.reduce((total, point, index) => {
    const next = points[(index + 1) % points.length];
    return total + point.x * next.y - next.x * point.y;
  }, 0);

  return Math.abs(doubleArea) / 2;
}

function csvValue(value: string | number | null) {
  return `"${String(value ?? '').replace(/"/g, '""')}"`;
}

export default function ManualColonyTracer({ previews }: ManualColonyTracerProps) {
  const [reviewer, setReviewer] = useState('');
  const [autoLoading, setAutoLoading] = useState(false);
  const timerRef = useRef<number | null>(null);
  const [autoPolygons, setAutoPolygons] = useState<Point[][]>([]);
  const [autoSeconds, setAutoSeconds] = useState<number | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [points, setPoints] = useState<Point[]>([]);
  const [drawing, setDrawing] = useState(false);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [umPerPx, setUmPerPx] = useState(DEFAULT_UM_PER_PX);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [previewError, setPreviewError] = useState(false);
  const [message, setMessage] = useState('');

  const selectedPreview = previews[selectedIndex];

  function resetTrace() {
    // Changing images always starts a fresh outline; saved measurements remain available for export.
    timerRef.current = null;
    setAutoPolygons([]);
    setAutoSeconds(null);
    setPoints([]);
    setDrawing(false);
    setImageSize({ width: 0, height: 0 });
    setPreviewError(false);
    setMessage('');
  }

  function selectImage(index: number) {
    setSelectedIndex(index);
    resetTrace();
  }

  const areaPx = useMemo(() => polygonArea(points), [points]);
  const areaUm2 = areaPx * umPerPx ** 2;
  const areaMm2 = areaUm2 / 1_000_000;
  const equivalentDiameterUm = 2 * Math.sqrt(areaUm2 / Math.PI);

  // Pointer coordinates are converted back to natural image pixels, so responsive display scaling
  // never changes the measured colony area.
  function pointerToImagePoint(event: ReactPointerEvent<SVGSVGElement>) {
    if (!imageSize.width || !imageSize.height) return null;

    const bounds = event.currentTarget.getBoundingClientRect();

    return {
      x: ((event.clientX - bounds.left) / bounds.width) * imageSize.width,
      y: ((event.clientY - bounds.top) / bounds.height) * imageSize.height,
    };
  }

  function addPoint(event: ReactPointerEvent<SVGSVGElement>) {
    const point = pointerToImagePoint(event);
    if (point) setPoints((current) => [...current, point]);
  }

  function saveMeasurement(note: Measurement['note']) {
    if (!selectedPreview) return;
    if (!reviewer.trim() || timerRef.current === null || !imageSize.width) {
      setMessage('Enter a reviewer ID, load the image, and start the timer before saving.'); return;
    }

    if (note === 'traced' && points.length < 3) {
      setMessage('Trace the colony outline with at least three points first.');
      return;
    }

    if (note === 'traced' && (!Number.isFinite(umPerPx) || umPerPx <= 0)) {
      setMessage('Enter a positive microns-per-pixel calibration first.');
      return;
    }

    const context = {
      reviewer: reviewer.trim(), elapsed_seconds: (performance.now() - timerRef.current) / 1000,
      width: imageSize.width, height: imageSize.height, page: selectedPreview.page + 1,
      um_per_px: umPerPx, points: note === 'traced' ? [...points] : [],
    };
    const measurement: Measurement =
      note === 'traced'
        ? {
            ...context,
            id: selectedIndex,
            file: selectedPreview.filename,
            area_px: areaPx,
            area_um2: areaUm2,
            area_mm2: areaMm2,
            equiv_diam_um: equivalentDiameterUm,
            note,
          }
        : {
            ...context,
            id: selectedIndex,
            file: selectedPreview.filename,
            area_px: null,
            area_um2: null,
            area_mm2: null,
            equiv_diam_um: null,
            note,
          };

    // Saving again replaces the prior decision for that selected upload, matching a redraw workflow.
    setMeasurements((current) => [
      ...current.filter((item) => item.id !== selectedIndex),
      measurement,
    ]);
    setPoints([]);
    setMessage(`${selectedPreview.filename} saved as ${note}.`);
  }

  function downloadMeasurements() {
    if (measurements.length === 0) {
      setMessage('Save at least one traced image or no-colony result first.');
      return;
    }

    const headers = [
      'file',
      'area_px',
      'area_um2',
      'area_mm2',
      'equiv_diam_um',
      'note', 'reviewer', 'elapsed_seconds', 'page', 'um_per_px',
    ];

    const rows = measurements
      .slice().sort((a, b) => a.id - b.id)
      .map((item) =>
        [
          item.file,
          item.area_px?.toFixed(2) ?? null,
          item.area_um2?.toFixed(2) ?? null,
          item.area_mm2?.toFixed(6) ?? null,
          item.equiv_diam_um?.toFixed(2) ?? null,
          item.note, item.reviewer, item.elapsed_seconds.toFixed(3), item.page, item.um_per_px,
        ]
          .map(csvValue)
          .join(',')
      );

    const blob = new Blob([[headers.join(','), ...rows].join('\n')], {
      type: 'text/csv',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'colony_sizes.csv';
    link.click();
    URL.revokeObjectURL(url);
  }

  function downloadRois() {
    const blob = new Blob([JSON.stringify({version: 1, annotations: measurements}, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = 'colony_rois.json'; link.click(); URL.revokeObjectURL(url);
  }

  async function suggestColony() {
    setAutoLoading(true);
    setAutoPolygons([]);
    setAutoSeconds(null);
    try {
      const form = new FormData(); form.append('file', selectedPreview.file);
      const response = await fetch(apiUrl(`/api/colony-detect?page=${selectedPreview.page}`), {
        method: 'POST', body: form, signal: AbortSignal.timeout(180000),
      });
      if (!response.ok) throw new Error(await apiError(response));
      const data: {polygons: number[][][]; elapsed_seconds: number} = await response.json();
      setAutoPolygons(data.polygons.map((polygon) => polygon.map(([x, y]) => ({x, y}))));
      setAutoSeconds(data.elapsed_seconds);
      setMessage(data.polygons.length ? 'Computer outlines shown in blue. Keep manual study traces independent.' : 'Computer found no colonies at this threshold.');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Colony detection failed.'); }
    finally { setAutoLoading(false); }
  }

  function downloadComputerRois() {
    const blob = new Blob([JSON.stringify({file: selectedPreview.filename, page: selectedPreview.page + 1,
      width: imageSize.width, height: imageSize.height, um_per_px: umPerPx,
      elapsed_seconds: autoSeconds, source: 'computer', polygons: autoPolygons}, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob); const link = document.createElement('a');
    link.href = url; link.download = 'computer_colony_rois.json'; link.click(); URL.revokeObjectURL(url);
  }

  if (!selectedPreview) return null;

  return (
    <section className="gl-card">
      <h2 className="gl-manual__title">Manual Colony Tracer</h2>
      <p className="gl-manual__hint">
        Draw directly over the colony. Measurements stay in this browser until you download the CSV.
      </p>

      <label>Reviewer ID <input className="gl-input" value={reviewer} onChange={(e) => setReviewer(e.target.value)} /></label>
      <button className="gl-btn gl-btn--primary" onClick={() => { timerRef.current = performance.now(); setMessage('Timer started; includes drawing and corrections until Keep Trace or No Colony.'); }}>Start image timer</button>
      <div className="gl-manual__controls">
        <label>
          Image
          <select
            className="gl-input"
            value={selectedIndex}
            onChange={(event) => selectImage(Number(event.target.value))}
          >
            {previews.map((preview, index) => (
              <option key={`${preview.filename}-${index}`} value={index}>
                {index + 1}. {preview.filename}
              </option>
            ))}
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
            onChange={(event) => setUmPerPx(Number(event.target.value))}
          />
        </label>
      </div>

      {previewError ? (
        <p className="gl-msg gl-msg--error">
          Image preview failed. Check the file and backend connection.
        </p>
      ) : (
        <div className="gl-manual__surface">
          <img
            src={selectedPreview.url}
            className="gl-manual__image"
            alt={`Manual tracing canvas for ${selectedPreview.filename}`}
            onLoad={(event) => {
              setImageSize({
                width: event.currentTarget.naturalWidth,
                height: event.currentTarget.naturalHeight,
              });
            }}
            onError={() => setPreviewError(true)}
          />

          {imageSize.width > 0 && (
            <svg
              className="gl-manual__overlay"
              viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
              onPointerDown={(event) => {
                event.preventDefault();
                event.currentTarget.setPointerCapture(event.pointerId);
                setPoints([]);
                setDrawing(true);
                addPoint(event);
              }}
              onPointerMove={(event) => {
                if (drawing) addPoint(event);
              }}
              onPointerUp={(event) => {
                setDrawing(false);
                event.currentTarget.releasePointerCapture(event.pointerId);
              }}
              onPointerCancel={() => setDrawing(false)}
            >
              {autoPolygons.map((polygon, index) => <polygon key={index} points={polygon.map((p) => `${p.x},${p.y}`).join(' ')} fill="none" stroke="blue" strokeWidth="2" />)}
              {points.length > 1 && (
                <polygon
                  points={points.map((point) => `${point.x},${point.y}`).join(' ')}
                  className="gl-manual__trace"
                />
              )}
            </svg>
          )}
        </div>
      )}

      <div className="gl-manual__metrics">
        <span>Area: {areaPx.toFixed(2)} px²</span>
        <span>Area: {areaUm2.toFixed(2)} µm²</span>
        <span>Equivalent diameter: {equivalentDiameterUm.toFixed(2)} µm</span>
      </div>

      <div className="gl-manual__actions">
        <button className="gl-btn gl-btn--primary" onClick={() => saveMeasurement('traced')}>
          Keep Trace
        </button>
        <button className="gl-btn gl-btn--primary" onClick={() => saveMeasurement('no colony')}>
          No Colony
        </button>
        <button className="gl-btn gl-btn--csv" onClick={() => setPoints([])}>
          Redraw
        </button>
        <button className="gl-btn gl-btn--csv" onClick={downloadMeasurements}>
          Download CSV ({measurements.length})
        </button>
      </div>

      <button className="gl-btn gl-btn--csv" disabled={!measurements.length} onClick={downloadRois}>Download training ROIs</button>
      <button className="gl-btn gl-btn--primary" disabled={autoLoading || !imageSize.width} onClick={suggestColony}>{autoLoading ? 'Circling…' : 'Auto circle (trained model)'}</button>
      <button className="gl-btn gl-btn--csv" disabled={autoSeconds === null} onClick={downloadComputerRois}>Download computer ROIs</button>
      {autoSeconds !== null && <p>Computer inference: {autoSeconds.toFixed(3)} seconds</p>}
      {message && <p className="gl-result-msg">{message}</p>}
    </section>
  );
}
