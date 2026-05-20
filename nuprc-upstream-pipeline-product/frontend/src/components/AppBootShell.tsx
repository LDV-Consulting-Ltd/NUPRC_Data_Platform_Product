"use client";

import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";

const StartupSplash = dynamic(() => import("./StartupSplash"), {
  ssr: false,
  loading: () => <motion.div className="fixed inset-0 z-[200] bg-[#050d1a]" aria-hidden />,
});

export default function AppBootShell({ children }: { children: React.ReactNode }) {
  const [splashDone, setSplashDone] = useState(false);

  return (
    <>
      <AnimatePresence mode="wait">
        {!splashDone && <StartupSplash key="splash" onComplete={() => setSplashDone(true)} />}
      </AnimatePresence>
      <motion.div
        className="min-h-screen"
        initial={false}
        animate={{ opacity: splashDone ? 1 : 0 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        style={{ visibility: splashDone ? "visible" : "hidden" }}
        aria-hidden={!splashDone}
      >
        {children}
      </motion.div>
    </>
  );
}
