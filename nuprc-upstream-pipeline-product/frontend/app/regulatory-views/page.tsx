import { redirectPreserving } from "../lib/preserve-redirect";

export default async function RegulatoryViewsRedirect({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  redirectPreserving("/regulatory", await searchParams);
}
