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
