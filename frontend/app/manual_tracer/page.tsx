'use client';

import { useEffect, useRef, useState } from 'react';
import ManualColonyTracer from '../dashboard/ManualColonyTracer';

type Preview = {
  filename: string;
  url: string;
};

export default function ManualTracerPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previews, setPreviews] = useState<Preview[]>([]);

  useEffect(() => {
    return () => {
      previews.forEach((preview) => URL.revokeObjectURL(preview.url));
    };
  }, [previews]);

  function handleFiles(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (files.length === 0) return;

    // Object URLs keep the feature frontend-only: uploaded images are never sent to the backend.
    setPreviews(
      files.map((file) => ({
        filename: file.name,
        url: URL.createObjectURL(file),
      }))
    );
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
          <input
            ref={fileInputRef}
            type="file"
            accept=".png,.jpg,.jpeg,.tif,.tiff"
            multiple
            onChange={handleFiles}
            style={{ display: 'none' }}
          />
          <button
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
