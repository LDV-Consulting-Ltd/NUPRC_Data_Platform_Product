export async function backendGet<T>(path: string): Promise<T> {
  const p = path.startsWith("/") ? path.slice(1) : path;
  const res = await fetch(`/api/backend/${p}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Backend GET failed: ${res.status}`);
  return res.json() as Promise<T>;
}
