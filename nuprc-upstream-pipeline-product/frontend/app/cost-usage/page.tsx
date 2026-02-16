"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function CostUsageRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/cost");
  }, [router]);
  return null;
}
