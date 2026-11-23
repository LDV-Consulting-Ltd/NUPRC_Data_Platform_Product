import { redirectPreserving } from "../lib/preserve-redirect";

export default async function TrustScoringRedirect({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  redirectPreserving("/trust", await searchParams);
}
