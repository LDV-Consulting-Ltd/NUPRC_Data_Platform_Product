"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function TrustScoringRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/trust");
  }, [router]);
  return null;
}
