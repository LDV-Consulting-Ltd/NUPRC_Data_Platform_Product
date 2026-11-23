/** Public NUPRC publication pages already used by this product's source configuration. */

export const COMPANY_SITE = "https://ldvconsultingltd.ng/";
export const NUPRC_REPORTS = "https://www.nuprc.gov.ng/reports";

export type PublicSource = {
  key: string;
  label: string;
  commodity: "Oil" | "Gas" | "Rig activity" | "Concession";
  unit: string;
  href: string;
  pageNote?: string;
};

export const PUBLIC_SOURCES: PublicSource[] = [
  {
    key: "oil_production_status",
    label: "Oil production status",
    commodity: "Oil",
    unit: "As published on the NUPRC oil production status page",
    href: "https://www.nuprc.gov.ng/oil-production-status-report/",
  },
  {
    key: "gas_production_status",
    label: "Gas production status",
    commodity: "Gas",
    unit: "As published on the NUPRC gas production status page",
    href: "https://www.nuprc.gov.ng/gas-production-status-report/",
  },
  {
    key: "rig_disposition",
    label: "Rig disposition",
    commodity: "Rig activity",
    unit: "Rig activity as published by NUPRC",
    href: "https://www.nuprc.gov.ng/rig-disposition-report/",
  },
  {
    key: "concession_situation",
    label: "Concession situation",
    commodity: "Concession",
    unit: "Concession situation as published by NUPRC",
    href: NUPRC_REPORTS,
    pageNote: "Concession files are published with NUPRC reports. This console does not host a separate official concession portal.",
  },
];

export function sourceByKey(key: string) {
  return PUBLIC_SOURCES.find((source) => source.key === key);
}
