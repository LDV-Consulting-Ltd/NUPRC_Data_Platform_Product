import { redirectPreserving } from "../lib/preserve-redirect";

export default async function DataCatalogRedirect({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  redirectPreserving("/catalog", await searchParams);
}
