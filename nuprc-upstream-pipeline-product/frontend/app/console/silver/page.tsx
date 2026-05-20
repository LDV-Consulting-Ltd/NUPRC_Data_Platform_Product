"use client";

import { Layers } from "lucide-react";
import LayerTablesView from "@/components/console/LayerTablesView";

export default function SilverPage() {
  return (
    <LayerTablesView
      layer="silver"
      title="Silver Layer"
      description="Standardized facts and dimensions ready for warehouse modeling."
      icon={Layers}
      accent="#2563eb"
    />
  );
}
