import { GapNote, PageHeader } from "../components/console/ui";

const sources = ["Oil Production", "Gas Production", "Rig Disposition", "Concession Status"];
const steps = ["Source", "Bronze", "Silver", "Warehouse", "Validate"];

export default function PipelineConfigPage() {
  return (
    <>
      <PageHeader
        title="Pipeline Config"
        description="The configured path for oil, gas, rig activity, and concession. Drag-and-drop editing is not connected to the pipeline service."
      />
      <GapNote>This canvas describes the existing pipeline. It does not save a new configuration or start a run.</GapNote>
      <div className="pc-split">
        <aside className="pc-filters">
          <p className="pc-nav-label">Sources</p>
          {sources.map((source) => (
            <div key={source} className="pc-step">
              <strong>{source}</strong>
            </div>
          ))}
        </aside>
        <div>
          <div className="pc-flow">
            {steps.map((step) => (
              <article key={step} className="pc-step">
                <div className="pc-step-k">Stage</div>
                <strong>{step}</strong>
                <p>Configured stage</p>
              </article>
            ))}
          </div>
          <section className="pc-card">
            <div className="pc-card-h">
              <h2>Validation rules</h2>
            </div>
            <div className="pc-card-b">
              <p>Schema checks, null checks, and range rules are described here. They are not editable from this screen.</p>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
