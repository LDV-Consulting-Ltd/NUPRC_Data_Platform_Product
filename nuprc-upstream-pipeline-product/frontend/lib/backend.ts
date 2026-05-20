export async function backendGet<T>(path: string): Promise<T> {
  const p = path.startsWith("/") ? path.slice(1) : path;
  const res = await fetch(`/api/backend/${p}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Backend GET failed: ${res.status}`);
  return res.json() as Promise<T>;
}

/** GET binary export (CSV/ZIP) and trigger browser download */
export async function backendDownload(path: string, filename: string): Promise<void> {
  const p = path.startsWith("/") ? path.slice(1) : path;
  const res = await fetch(`/api/backend/${p}`, { cache: "no-store" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Download failed: ${res.status}`);
  }
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition");
  const match = disposition?.match(/filename="?([^";\n]+)"?/);
  const name = match?.[1] ?? filename;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
