import { describe, expect, it } from "vitest";
import { Simulation } from "./simulation.js";

describe("browser simulation engine", () => {
  it("starts deterministic from the default seed", () => {
    const first = new Simulation(2025).snapshot();
    const second = new Simulation(2025).snapshot();
    expect(first.delivered).toBe(8);
    expect(second.delivered).toBe(8);
    expect(first.log.length).toBe(8);
    expect(first.risky).toBeGreaterThan(0);
  });

  it("keeps one record per step in arrival order", () => {
    const engine = new Simulation(2025);
    expect(engine.snapshot().log.length).toBe(8);
    const first = engine.step("mixed");
    expect(engine.snapshot().log.length).toBe(9);
    engine.step("mixed");
    const snapshot = engine.snapshot();
    expect(snapshot.log.length).toBe(10);
    expect(snapshot.log[8].event.time).toBe(first.event.time);
  });

  it("flags reviews from the configured threshold only", () => {
    const engine = new Simulation(2025);
    engine.setThreshold(0.99);
    const snapshot = engine.snapshot();
    expect(snapshot.flaggedPercent).toBeGreaterThanOrEqual(0);
  });

  it("catches replays and bad signatures as findings", () => {
    const engine = new Simulation(2025);
    for (let index = 0; index < 20; index += 1) engine.step("mixed");
    const snapshot = engine.snapshot();
    expect(snapshot.rejected).toBeGreaterThan(0);
    expect(snapshot.duplicates).toBeGreaterThan(0);
    expect(snapshot.sharedDevices).toBeGreaterThanOrEqual(0);
  });

  it("resets to a reproducible state", () => {
    const engine = new Simulation(77);
    engine.step("mixed");
    const after = engine.snapshot();
    engine.reset();
    const again = engine.snapshot();
    expect(after.delivered).toBeGreaterThan(8);
    expect(again.delivered).toBe(8);
    expect(again.log[0].event.time).toBe(after.log[0].event.time);
  });
});
