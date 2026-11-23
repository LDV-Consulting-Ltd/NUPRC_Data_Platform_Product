import { redirectPreserving } from "../lib/preserve-redirect";

export default async function LineageExplorerRedirect({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  redirectPreserving("/lineage", await searchParams);
}
