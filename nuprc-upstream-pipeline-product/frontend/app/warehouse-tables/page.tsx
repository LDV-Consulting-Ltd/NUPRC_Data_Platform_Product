"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function WarehouseTablesRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/showcase/warehouse");
  }, [router]);
  return null;
}
