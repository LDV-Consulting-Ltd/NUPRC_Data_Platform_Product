async function backendError(res: Response): Promise<Error> {
  let detail = "";
  try {
    const body = await res.json();
    if (body && typeof body.detail === "string") detail = body.detail;
    else if (body && Array.isArray(body.detail)) detail = body.detail.map((e: any) => e?.msg ?? e).join("; ");
    else if (body && typeof body.detail === "object") detail = JSON.stringify(body.detail);
  } catch {
    detail = await res.text() || res.statusText;
  }
  const msg = detail
    ? `Backend ${res.status}: ${detail}`
    : `Backend ${res.status} ${res.statusText}`;
  return new Error(msg);
}

export async function backendGet<T>(path: string): Promise<T> {
  const res = await fetch(`/api/backend${path}`, { cache: "no-store" });
  if (!res.ok) throw await backendError(res);
  return res.json() as Promise<T>;
}

export async function backendPost<T>(path: string, body?: any): Promise<T> {
  const res = await fetch(`/api/backend${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  if (!res.ok) throw await backendError(res);
  return res.json() as Promise<T>;
}

/** GET binary export (CSV/ZIP) and trigger browser download */
export async function backendDownload(path: string, filename: string): Promise<void> {
  const p = path.startsWith("/") ? path : `/${path}`;
  const res = await fetch(`/api/backend${p}`, { cache: "no-store" });
  if (!res.ok) throw await backendError(res);
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
