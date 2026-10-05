'use client';

import { useEffect, useRef, useState } from 'react';
import { previewUrls } from '@/lib/images';
import ManualColonyTracer from '../dashboard/ManualColonyTracer';

type Preview = {
  filename: string;
  url: string;
  file: File;
  page: number;
};

export default function ManualTracerPage() {
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previews, setPreviews] = useState<Preview[]>([]);

  useEffect(() => {
    return () => {
      previews.forEach((preview) => URL.revokeObjectURL(preview.url));
    };
  }, [previews]);

  async function handleFiles(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (files.length === 0) return;

    setLoading(true);
    setError('');
    try {
      const urls = await previewUrls(files, page - 1);
      setPreviews(files.map((file, index) => ({filename: file.name, url: urls[index], file, page: page - 1})));
    } catch (error) { setError(error instanceof Error ? error.message : 'Preview failed.'); }
    finally { setLoading(false); }

  }

  return (
    <main className="gl-page">
      <div className="gl-container">
        <nav className="gl-nav">
          <h1 className="gl-nav__title">Manual Colony Tracer</h1>
          <div className="gl-nav__links">
            <a href="/dashboard" className="gl-nav__link">Back to Dashboard</a>
          </div>
        </nav>

        <section className="gl-card">
          <p className="gl-upload__label">Upload cell images for manual tracing (PNG, JPG, JPEG, TIFF)</p>
          <label>Image page <input className="gl-input" type="number" min="1" value={page} disabled={loading} onChange={(e) => setPage(Math.max(1, Number(e.target.value) || 1))} /></label>
          <p>TIFFs are sent to the backend for PNG previews at the original pixel dimensions.</p>
          {error && <p role="alert">{error}</p>}
          <input
            ref={fileInputRef}
            type="file"
            accept=".png,.jpg,.jpeg,.tif,.tiff"
            multiple
            onChange={handleFiles}
            style={{ display: 'none' }}
          />
          <button
            disabled={loading}
            className="gl-btn gl-btn--primary"
            onClick={() => fileInputRef.current?.click()}
          >
            Choose Images to Trace
          </button>
        </section>

        {previews.length > 0 && (
          <ManualColonyTracer
            key={previews.map((preview) => preview.url).join('|')}
            previews={previews}
          />
        )}
      </div>
    </main>
  );
}
