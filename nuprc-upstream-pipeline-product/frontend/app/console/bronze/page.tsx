"use client";

import { Database } from "lucide-react";
import LayerTablesView from "@/components/console/LayerTablesView";

export default function BronzePage() {
  return (
    <LayerTablesView
      layer="bronze"
      title="Bronze Layer"
      description="Raw ingested tables (JSONB and ETL staging) in the bronze schema."
      icon={Database}
      accent="#f59e0b"
    />
  );
}
