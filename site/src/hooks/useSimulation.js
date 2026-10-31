import { useCallback, useEffect, useRef, useState } from "react";
import { Simulation } from "../lib/simulation.js";

/**
 * React binding for the deterministic simulator.
 *
 * The engine lives in a ref so re-renders never replay history. Every action
 * takes a fresh snapshot, and the auto-traffic timer is the only side effect.
 */
export function useSimulation() {
  const engineRef = useRef(null);
  if (engineRef.current === null) engineRef.current = new Simulation();
  const engine = engineRef.current;
  const [snapshot, setSnapshot] = useState(() => engine.snapshot());
  const [mode, setMode] = useState("mixed");
  const prefersReduced =
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const [auto, setAuto] = useState(!prefersReduced);
  const [motion, setMotion] = useState(!prefersReduced);

  const refresh = useCallback(() => {
    setSnapshot(engine.snapshot());
  }, [engine]);

  const step = useCallback(
    (scenario = "mixed", options = {}) => {
      const record = engine.step(scenario, options);
      refresh();
      return record;
    },
    [engine, refresh],
  );

  const force = useCallback(
    (scenario) => {
      let record = null;
      if (scenario === "shared device") {
        for (let index = 0; index < 5; index += 1) {
          record = engine.step("shared device", {
            device: "hub_0",
            account: (index * 5 + 3) % 24,
          });
        }
      } else if (scenario === "replay") {
        engine.step("normal");
        engine.step("normal");
        record = engine.step("replay");
      } else {
        record = engine.step(scenario);
      }
      if (record) engine.pin(record);
      refresh();
    },
    [engine, refresh],
  );

  const burst = useCallback(() => {
    for (let index = 0; index < 20; index += 1) engine.step("mixed");
    refresh();
  }, [engine, refresh]);

  const reset = useCallback(() => {
    engine.reset();
    refresh();
  }, [engine, refresh]);

  const setThreshold = useCallback(
    (value) => {
      engine.setThreshold(value);
      refresh();
    },
    [engine, refresh],
  );

  const pin = useCallback(
    (record) => {
      engine.pin(record);
      refresh();
    },
    [engine, refresh],
  );

  const follow = useCallback(() => {
    engine.follow();
    refresh();
  }, [engine, refresh]);

  const reason = useCallback((record) => engine.reason(record), [engine]);
  const isReview = useCallback((record) => engine.isReview(record), [engine]);

  const toggleMotion = useCallback(() => {
    setMotion((current) => {
      const next = !current;
      setAuto(next);
      return next;
    });
  }, []);

  useEffect(() => {
    if (!auto || !motion) return undefined;
    const timer = window.setInterval(() => {
      if (document.hidden) return;
      engine.step(mode);
      refresh();
    }, 1400);
    return () => window.clearInterval(timer);
  }, [auto, motion, mode, engine, refresh]);

  return {
    snapshot,
    mode,
    setMode,
    auto,
    setAuto,
    motion,
    toggleMotion,
    step,
    force,
    burst,
    reset,
    setThreshold,
    pin,
    follow,
    reason,
    isReview,
  };
}
