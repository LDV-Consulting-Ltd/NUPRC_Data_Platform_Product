import { redirect } from "next/navigation";

type Search = Record<string, string | string[] | undefined>;

export function redirectPreserving(path: string, params: Search): never {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === "string") query.set(key, value);
    else if (Array.isArray(value)) value.forEach((item) => query.append(key, item));
  }
  const qs = query.toString();
  redirect(qs ? `${path}?${qs}` : path);
}
