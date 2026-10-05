export function apiUrl(path: string) {
  const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '');
  if (!base) throw new Error('API URL is missing. Set NEXT_PUBLIC_API_URL and rebuild the frontend.');
  return `${base}${path}`;
}

export async function apiError(response: Response) {
  const body = await response.text();
  try {
    const parsed = JSON.parse(body);
    if (typeof parsed.detail === 'string') return parsed.detail;
  } catch { /* A proxy may return HTML instead of JSON. */ }
  return `Request failed (${response.status}). Check backend availability and logs.`;
}

export async function previewUrl(file: File, page = 0): Promise<string> {
  if (!/\.tiff?$/i.test(file.name)) return URL.createObjectURL(file);
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(apiUrl(`/api/image-preview?page=${page}`), {
    method: 'POST', body: form, signal: AbortSignal.timeout(60000),
  });
  if (!response.ok) throw new Error(await apiError(response));
  return URL.createObjectURL(await response.blob());
}

export async function previewUrls(files: File[], page: number) {
  const urls: string[] = [];
  try {
    // Sequential conversion makes cleanup deterministic if any image fails.
    for (const file of files) urls.push(await previewUrl(file, page));
    return urls;
  } catch (error) {
    urls.forEach((url) => URL.revokeObjectURL(url));
    throw error;
  }
}
