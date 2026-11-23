import { redirectPreserving } from "../lib/preserve-redirect";

export default async function CostUsageRedirect({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  redirectPreserving("/cost", await searchParams);
}
