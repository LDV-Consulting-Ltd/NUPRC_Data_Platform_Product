"use client";

import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const MIN_DURATION_MS = 2800;
const MAX_WAIT_MS = 9000;
const FADE_OUT_MS = 700;
const HEALTH_POLL_MS = 400;

type StartupSplashProps = {
  onComplete: () => void;
};

async function fetchBackendHealthy(): Promise<boolean> {
  try {
    const res = await fetch("/api/backend/health/summary", { cache: "no-store" });
    if (!res.ok) return false;
    const data = (await res.json()) as { ok?: boolean; status?: string };
    return data.ok === true;
  } catch {
    return false;
  }
}

function ParticleField({ reducedMotion }: { reducedMotion: boolean }) {
  const particles = useMemo(
    () =>
      Array.from({ length: 28 }, (_, i) => ({
        id: i,
        left: `${(i * 17 + 7) % 100}%`,
        top: `${(i * 23 + 11) % 100}%`,
        size: 2 + (i % 3),
        delay: (i % 7) * 0.35,
        duration: 4 + (i % 5) * 0.8,
      })),
    []
  );

  if (reducedMotion) return null;

  return (
    <motion.div
      className="pointer-events-none absolute inset-0 overflow-hidden"
      aria-hidden
      initial={{ opacity: 0 }}
      animate={{ opacity: 0.55 }}
      transition={{ duration: 1.2 }}
    >
      {particles.map((p) => (
        <motion.span
          key={p.id}
          className="absolute rounded-full bg-cyan-400/70"
          style={{
            left: p.left,
            top: p.top,
            width: p.size,
            height: p.size,
            willChange: "transform, opacity",
          }}
          animate={{
            y: [0, -28, 0],
            x: [0, 12, 0],
            opacity: [0.15, 0.75, 0.2],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </motion.div>
  );
}

function EnergyGrid({ reducedMotion }: { reducedMotion: boolean }) {
  return (
    <div
      className={`pointer-events-none absolute inset-0 opacity-30 ${reducedMotion ? "" : "splash-energy-grid"}`}
      aria-hidden
    >
      <svg className="h-full w-full" preserveAspectRatio="none" viewBox="0 0 1200 800">
        <defs>
          <linearGradient id="gridFade" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.05" />
            <stop offset="50%" stopColor="#22d3ee" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.05" />
          </linearGradient>
        </defs>
        {Array.from({ length: 13 }).map((_, i) => (
          <line
            key={`v-${i}`}
            x1={i * 100}
            y1={0}
            x2={i * 100}
            y2={800}
            stroke="url(#gridFade)"
            strokeWidth="1"
          />
        ))}
        {Array.from({ length: 9 }).map((_, i) => (
          <line
            key={`h-${i}`}
            x1={0}
            y1={i * 100}
            x2={1200}
            y2={i * 100}
            stroke="url(#gridFade)"
            strokeWidth="1"
          />
        ))}
      </svg>
    </div>
  );
}

export default function StartupSplash({ onComplete }: StartupSplashProps) {
  const reducedMotion = useReducedMotion();
  const [exiting, setExiting] = useState(false);
  const completedRef = useRef(false);
  const mountedAt = useRef(Date.now());
  const healthOkRef = useRef(false);

  const finish = useCallback(() => {
    if (completedRef.current) return;
    completedRef.current = true;
    setExiting(true);
    window.setTimeout(() => {
      document.documentElement.style.overflow = "";
      onComplete();
    }, FADE_OUT_MS);
  }, [onComplete]);

  useEffect(() => {
    document.documentElement.style.overflow = "hidden";

    let cancelled = false;
    const poll = async () => {
      while (!cancelled && !healthOkRef.current) {
        const ok = await fetchBackendHealthy();
        if (ok) healthOkRef.current = true;
        if (!healthOkRef.current) await new Promise((r) => window.setTimeout(r, HEALTH_POLL_MS));
      }
    };
    poll();

    const tick = window.setInterval(() => {
      const elapsed = Date.now() - mountedAt.current;
      const minMet = elapsed >= MIN_DURATION_MS;
      const maxMet = elapsed >= MAX_WAIT_MS;
      if ((minMet && healthOkRef.current) || maxMet) {
        window.clearInterval(tick);
        finish();
      }
    }, 120);

    return () => {
      cancelled = true;
      window.clearInterval(tick);
      document.documentElement.style.overflow = "";
    };
  }, [finish]);

  const imageScale = reducedMotion ? 1 : exiting ? 1 : [1.18, 1];
  const containerOpacity = exiting ? 0 : 1;

  return (
    <motion.div
      className="fixed inset-0 z-[200] flex flex-col items-center justify-center bg-[#050d1a]"
      role="status"
      aria-live="polite"
      aria-label="Initializing PetroCore"
      initial={{ opacity: 1 }}
      animate={{ opacity: containerOpacity }}
      transition={{ duration: FADE_OUT_MS / 1000, ease: [0.22, 1, 0.36, 1] }}
      style={{ willChange: "opacity" }}
    >
      <motion.div
        className="pointer-events-none absolute inset-0 bg-gradient-to-br from-[#050d1a] via-[#0a1628] to-[#0f2744]"
        aria-hidden
      />
      <EnergyGrid reducedMotion={!!reducedMotion} />
      <ParticleField reducedMotion={!!reducedMotion} />

      <div className="relative z-10 flex w-full max-w-[min(96vw,1200px)] flex-col items-center px-6">
        <motion.div
          className="relative aspect-[16/9] w-full overflow-hidden rounded-2xl border border-cyan-500/20 shadow-[0_0_80px_rgba(34,211,238,0.15)]"
          initial={reducedMotion ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 1.18 }}
          animate={
            reducedMotion
              ? { opacity: 1, scale: 1 }
              : { opacity: 1, scale: imageScale, boxShadow: ["0 0 40px rgba(34,211,238,0.12)", "0 0 90px rgba(34,211,238,0.28)", "0 0 50px rgba(34,211,238,0.16)"] }
          }
          transition={{
            duration: reducedMotion ? 0.3 : 3.2,
            ease: [0.16, 1, 0.3, 1],
            boxShadow: { duration: 2.4, repeat: exiting ? 0 : Infinity, repeatType: "mirror" },
          }}
          style={{ willChange: "transform, opacity" }}
        >
          <Image
            src="/petrocore-hero.png"
            alt="LDV Consulting Ltd and PetroCore Upstream Governance and Intelligence Platform"
            fill
            priority
            className="object-cover object-center"
            sizes="(max-width: 768px) 96vw, 1200px"
          />
          <motion.div
            className="absolute inset-0 bg-gradient-to-tr from-[#050d1a]/50 via-transparent to-cyan-500/15"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.4, ease: "easeOut" }}
            aria-hidden
          />
          <motion.div
            className="pointer-events-none absolute inset-0 ring-1 ring-inset ring-cyan-400/20"
            animate={reducedMotion ? {} : { opacity: [0.35, 0.85, 0.4] }}
            transition={{ duration: 2.2, repeat: Infinity, repeatType: "mirror", ease: "easeInOut" }}
            aria-hidden
          />
        </motion.div>

        <motion.p
          className="mt-8 max-w-lg text-center text-sm font-medium tracking-wide text-cyan-100/90 sm:text-base"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: [0.45, 0.95, 0.5], y: 0 }}
          transition={{ duration: 2.4, repeat: Infinity, repeatType: "mirror", ease: "easeInOut", delay: 0.4 }}
        >
          Initializing PetroCore Intelligence Platform...
        </motion.p>
      </div>
    </motion.div>
  );
}
