import Link from "next/link";

export default function NotFound() {
  return (
    <div className="pc-state pc-state-empty" role="status">
      <h2>This page is not in the console</h2>
      <div className="pc-state-body">
        <p>The address does not match a production route.</p>
        <p>
          <Link href="/">Landing page</Link>
          {" · "}
          <Link href="/control-panel">Control Panel</Link>
        </p>
      </div>
    </div>
  );
}
