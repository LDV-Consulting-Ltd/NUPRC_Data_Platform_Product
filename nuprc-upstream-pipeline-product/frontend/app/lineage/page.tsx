import Link from "next/link";
import { PUBLIC_SOURCES } from "@/lib/public-sources";
import { GapNote, PageHeader } from "../components/console/ui";

const nodes = [
  { id: "nuprc_oil", label: "NUPRC Oil", layer: "Source" },
  { id: "nuprc_gas", label: "NUPRC Gas", layer: "Source" },
  { id: "bronze_oil", label: "bronze.oil_production_status_raw", layer: "Bronze" },
  { id: "silver_oil", label: "silver.oil_production", layer: "Silver" },
  { id: "wh_fact", label: "warehouse.fact_oil_production", layer: "Warehouse" },
];

export default function LineagePage() {
  return (
    <>
      <PageHeader
        title="Lineage"
        description="Source reports flow through bronze and silver into the warehouse. Oil and gas stay on separate source nodes."
      />
      <div className="pc-flow">
        {nodes.map((node) => (
          <article key={node.id} className="pc-step">
            <div className="pc-step-k">{node.layer}</div>
            <strong>{node.label}</strong>
          </article>
        ))}
      </div>
      <div className="pc-legend">
        <span><i className="pc-swatch" style={{ background: "#93a6b8" }} /> Source</span>
        <span><i className="pc-swatch" style={{ background: "#c4a35a" }} /> Bronze</span>
        <span><i className="pc-swatch" style={{ background: "#0f4c75" }} /> Silver</span>
        <span><i className="pc-swatch" style={{ background: "#146c43" }} /> Warehouse</span>
      </div>
      <GapNote>An interactive graph is not returned by the API. The nodes above are the existing lineage map for this screen.</GapNote>
      <section className="pc-card">
        <div className="pc-card-h">
          <h2>Evidence</h2>
        </div>
        <div className="pc-card-b">
          <ul>
            {PUBLIC_SOURCES.map((source) => (
              <li key={source.key}>
                {source.commodity}:{" "}
                <a href={source.href} target="_blank" rel="noopener noreferrer">
                  {source.label}
                </a>
              </li>
            ))}
          </ul>
          <p>
            <Link href="/showcase/diagrams">Open the isolated legacy lineage fixture</Link>
          </p>
        </div>
      </section>
    </>
  );
}
