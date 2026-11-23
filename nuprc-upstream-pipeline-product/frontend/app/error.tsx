"use client";

import { useEffect } from "react";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  const denied = /401|403|forbidden|unauthorized/i.test(error.message ?? "");

  return (
    <div className={denied ? "pc-state pc-state-error" : "pc-state pc-state-error"} role="alert">
      <h2>{denied ? "You do not have access to this view" : "This page could not be loaded"}</h2>
      <div className="pc-state-body">
        <p>{denied ? "The workspace refused this request." : error.message || "An unexpected error occurred."}</p>
        <p>
          <button type="button" className="pc-btn" onClick={reset}>
            Try again
          </button>
        </p>
      </div>
    </div>
  );
}
