"use client";

import { FolderTree } from "lucide-react";
import LayerTablesView from "@/components/console/LayerTablesView";

export default function MetadataPage() {
  return (
    <LayerTablesView
      layer="meta"
      title="Metadata Registry"
      description="Pipeline runs, file registry, schema drift, and diagram metadata."
      icon={FolderTree}
      accent="#6366f1"
    />
  );
}
