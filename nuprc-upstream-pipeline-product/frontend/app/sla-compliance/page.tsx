"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function SLAComplianceRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/sla");
  }, [router]);
  return null;
}
