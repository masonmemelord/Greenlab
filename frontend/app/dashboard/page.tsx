'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import '@/app/globals.css';
import { apiUrl, apiError, previewUrls } from '@/lib/images';

//Should be self explanatory
type DetectionResult = {
  filename: string;
  image: string;
  cell_count: number;
  elapsed_seconds: number;
};

type PreviewImage = {
  filename: string;
  url: string;
};

type HistoryItem = {
  filename: string;
  cell_count: number;
  confidence: number;
  timestamp: string;
};

export default function Dashboard() {
  const router = useRouter();

  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [images, setImages] = useState<File[]>([]);
  const [previews, setPreviews] = useState<PreviewImage[]>([]);
  const [results, setResults] = useState<DetectionResult[]>([]);
  const [confidence, setConfidence] = useState(0.5);
  const [loading, setLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    return () => {
      previews.forEach((preview) => URL.revokeObjectURL(preview.url));
    };
  }, [previews]);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files ?? []);
    if (selectedFiles.length === 0) return;

    setError('');
    setLoading(true);
    try {
      const urls = await previewUrls(selectedFiles, page - 1);
      setImages(selectedFiles);
      setPreviews(selectedFiles.map((file, index) => ({ filename: file.name, url: urls[index] })));
      setResults([]);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Image preview failed.');
    } finally { setLoading(false); }

  };

  const handleDetect = async () => {
    if (images.length === 0) return;

    setLoading(true);
    setError('');
    setResults([]);

    try {
      const formData = new FormData();

      images.forEach((image) => {
        formData.append('files', image);
      });

      const res = await fetch( //waits for FastAPI to complete its backend call
        apiUrl(`/api/detect?confidence=${confidence}&page=${page - 1}`),
        {
          method: 'POST',
          body: formData,
          signal: AbortSignal.timeout(180000),
        }
      );

      if (!res.ok) throw new Error(await apiError(res));

      const data: { results: DetectionResult[]; total_files: number } = await res.json();

      if (!Array.isArray(data.results) || data.results.length !== images.length) throw new Error('Backend returned incomplete results.');
      setResults(data.results);

      setHistory((prev) => [  //fetches history of files (ie. prev and data.results)
        ...prev,
        ...data.results.map((item) => ({
          filename: item.filename,
          cell_count: item.cell_count,
          confidence,
          timestamp: new Date().toLocaleString(),
        })),
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Detection failed. Check the backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const downloadCSV = () => { //Downloads CSV logs
    const escapeCSV = (value: string | number) =>
      `"${String(value).replace(/"/g, '""')}"`;

    const headers = ['Filename', 'Cell Count', 'Confidence', 'Timestamp']; //what specifiers fall under it
    const rows = history.map((h) =>
      [h.filename, h.cell_count, h.confidence, h.timestamp]
        .map(escapeCSV)
        .join(',')
    );

    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');

    a.href = url;
    a.download = 'greenlab_results.csv';
    a.click();

    URL.revokeObjectURL(url);
  };

  const handleLogout = () => {
    localStorage.removeItem('authenticated');
    router.push('/');
  };

  const totalCells = results.reduce((sum, item) => sum + item.cell_count, 0); //basic math for number of cells found

  return (
    <main className="gl-page">
      <div className="gl-container">

        {/* Navbar */}
        <nav className="gl-nav">
          <h1 className="gl-nav__title">Greenlab Cell Detection</h1>
          <div className="gl-nav__links">
            <a href="https://sse.tulane.edu/bme/about" target="_blank" className="gl-nav__link">Tulane BME</a>
            <a href="/manual_tracer" className="gl-nav__link">Manual Tracer</a>
            <a href="/cell_sizer" className="gl-nav__link">Cell Sizer</a>
            <a href="/settings" className="gl-nav__link">Settings</a>
            <button onClick={handleLogout} className="gl-btn gl-btn--primary">Log Out</button>
          </div>
        </nav>

        {/* Upload Card */}
        <div className="gl-card">
          <p className="gl-upload__label">Upload cell images (PNG, JPG, JPEG, TIFF)</p>

          <label>Image page (1 for single-page images) <input className="gl-input" type="number" min="1" value={page} disabled={loading || images.length > 0} onChange={(e) => setPage(Math.max(1, Number(e.target.value) || 1))} /></label>
          <p>To change pages, reload this page before choosing images.</p>
          {error && <p role="alert" className="gl-msg gl-msg--error">{error}</p>}
          <input
            ref={fileRef}
            type="file"
            accept=".png,.jpg,.jpeg,.tif,.tiff"
            multiple
            onChange={handleFile}
            style={{ display: 'none' }}
          />

          <button
            disabled={loading}
            onClick={() => fileRef.current?.click()}
            className="gl-btn gl-btn--primary"
          >
            Choose Images
          </button>

          {previews.length > 0 && (
            <>
              <p className="gl-result-msg">
                Selected {previews.length} image{previews.length === 1 ? '' : 's'}
              </p>

              {previews.map((preview, index) => {
                const result = results[index];

                return (
                  <div
                    key={`${preview.filename}-${index}`}
                    className="gl-upload__grid"
                    style={{ marginTop: '1rem' }}
                  >
                    <div>
                      <p className="gl-upload__img-label">
                        Original: {preview.filename}
                      </p>
                      <img
                        src={preview.url}
                        className="gl-upload__img"
                        alt={`Original upload ${preview.filename}`}
                      />
                    </div>

                    {result && (
                      <div>
                        <p className="gl-upload__img-label">
                          Detection Result: {result.cell_count} cell(s) · {result.elapsed_seconds.toFixed(2)} s
                        </p>
                        <img
                          src={`data:image/jpeg;base64,${result.image}`}
                          className="gl-upload__img"
                          alt={`Detection result for ${result.filename}`}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </>
          )}
        </div>

        {/* Confidence + Detect */}
        {previews.length > 0 && (
          <div className="gl-card">
            <label className="gl-slider__label">
              Confidence Threshold:{' '}
              <span className="gl-slider__value">{confidence}</span>
            </label>

            <input
              type="range"
              min={0.1}
              max={0.9}
              step={0.05}
              value={confidence}
              onChange={(e) => setConfidence(Number(e.target.value))}
              className="gl-slider"
            />

            <button
              onClick={handleDetect}
              disabled={loading}
              className="gl-btn gl-btn--detect"
            >
              {loading ? 'Detecting...' : 'Detect Cells'}
            </button>

            {results.length > 0 && (
              <p className="gl-result-msg">
                Processed {results.length} image{results.length === 1 ? '' : 's'} · Found {totalCells} total cell(s)
              </p>
            )}
          </div>
        )}
      </div>

      {/* History Table */}
      {history.length > 0 && (
        <div className="gl-card" style={{ margin: '1.5rem auto', maxWidth: '64rem' }}>
          <div className="gl-history__header">
            <h2 className="gl-history__title">Detection History</h2>
            <button onClick={downloadCSV} className="gl-btn gl-btn--csv">Download CSV</button>
          </div>

          <table className="gl-table">
            <thead>
              <tr>
                <th>File</th>
                <th>Cells Found</th>
                <th>Confidence</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h, i) => (
                <tr key={`${h.filename}-${i}`}>
                  <td>{h.filename}</td>
                  <td className="gl-table__count">{h.cell_count}</td>
                  <td>{h.confidence}</td>
                  <td>{h.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer */}
      <footer className="gl-footer">
        <p className="gl-footer__body">
          Greenlab is a Tulane University research tool for automated AI cell detection and analysis using deep learning. Upload microscopy images to detect and count cells with precision.
        </p>
        <p className="gl-footer__copy">© 2026 Greenlab · Tulane University 🌊</p>
        <a href="https://portfolio-site-wheat-delta.vercel.app" target="_blank" className="gl-footer__link">Built by Mason Mitchell</a>
        <p className="gl-footer__disclaimer">Please Note: Greenlab is still in development. Accurate results are not guaranteed</p>
      </footer>
    </main>
  );
}
