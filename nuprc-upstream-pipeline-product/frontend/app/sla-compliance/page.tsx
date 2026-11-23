import { redirectPreserving } from "../lib/preserve-redirect";

export default async function SLAComplianceRedirect({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  redirectPreserving("/sla", await searchParams);
}
