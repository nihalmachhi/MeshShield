import DecisionFeed from "./DecisionFeed.jsx";

const SCENARIOS = [
    { key: "mixed", label: "Mixed" },
    { key: "shared device", label: "Shared device" },
    { key: "replay", label: "Replay" },
    { key: "bad signature", label: "Bad signature" },
    { key: "high amount", label: "High amount" },
];

export default function Simulator({ sim }) {
    const { snapshot } = sim;
    const threshold = snapshot.threshold;
    const precision =
        snapshot.precision === null ? "–" : snapshot.precision.toFixed(2);
    const recall = snapshot.recall === null ? "–" : snapshot.recall.toFixed(2);

    return (
        <div className="stage" id="demo">
            <div
                className="ui"
                role="group"
                aria-label="Simulated MeshShield review dashboard"
            >
                <div className="ui-bar">
                    <div className="ui-title">
                        <span className="live" aria-hidden="true" />
                        MeshShield <small>simulated review dashboard</small>
                    </div>
                    <div className="kpis">
                        <div>
                            <b>{snapshot.delivered}</b>
                            <span>payments</span>
                        </div>
                        <div>
                            <b>{snapshot.reviewPercent}%</b>
                            <span>in review</span>
                        </div>
                        <div>
                            <b>{snapshot.duplicates}</b>
                            <span>replays caught</span>
                        </div>
                    </div>
                </div>
                <div className="ctl">
                    <div
                        className="seg"
                        role="radiogroup"
                        aria-label="Traffic scenario"
                    >
                        {SCENARIOS.map((scenario) => (
                            <button
                                key={scenario.key}
                                type="button"
                                role="radio"
                                aria-checked={sim.mode === scenario.key}
                                onClick={() => sim.setMode(scenario.key)}
                            >
                                {scenario.label}
                            </button>
                        ))}
                    </div>
                    <div className="acts">
                        <button
                            className="ab"
                            type="button"
                            aria-pressed={sim.auto}
                            onClick={() => sim.setAuto(!sim.auto)}
                        >
                            Auto traffic
                        </button>
                        <button
                            className="ab pri"
                            type="button"
                            onClick={sim.burst}
                        >
                            Send 20 payments
                        </button>
                        <button
                            className="ab"
                            type="button"
                            onClick={sim.reset}
                        >
                            Reset
                        </button>
                    </div>
                </div>
                <div className="main">
                    <div className="stack">
                        <div className="bk">
                            <div className="bk-h">
                                <h3>Sync queue</h3>
                                <span className="pill ok">idempotent</span>
                            </div>
                            <dl className="m">
                                <div>
                                    <dt>Delivered</dt>
                                    <dd>{snapshot.delivered}</dd>
                                </div>
                                <div>
                                    <dt>Accepted</dt>
                                    <dd>{snapshot.accepted}</dd>
                                </div>
                                <div>
                                    <dt>Duplicates</dt>
                                    <dd>{snapshot.duplicates}</dd>
                                </div>
                                <div>
                                    <dt>Rejected</dt>
                                    <dd>{snapshot.rejected}</dd>
                                </div>
                            </dl>
                            <span className="bar">
                                <i
                                    style={{
                                        width: `${
                                            snapshot.delivered
                                                ? (snapshot.accepted /
                                                      snapshot.delivered) *
                                                  100
                                                : 0
                                        }%`,
                                    }}
                                />
                            </span>
                        </div>
                        <div className="bk">
                            <div className="bk-h">
                                <h3>Device graph</h3>
                                <span
                                    className={`pill ${
                                        snapshot.sharedDevices ? "bad" : "ok"
                                    }`}
                                >
                                    {snapshot.sharedDevices} shared
                                </span>
                            </div>
                            <dl className="m">
                                {snapshot.deviceRows.map((row) => (
                                    <div key={row.device}>
                                        <dt>{row.device}</dt>
                                        <dd>
                                            {row.accounts}
                                            {row.accounts === 1
                                                ? " acct"
                                                : " accts"}
                                        </dd>
                                    </div>
                                ))}
                            </dl>
                        </div>
                        <div className="bk">
                            <div className="bk-h">
                                <h3>Review threshold</h3>
                                <span className="pill warn">
                                    {threshold.toFixed(2)}
                                </span>
                            </div>
                            <input
                                className="rng"
                                type="range"
                                min="0.3"
                                max="0.8"
                                step="0.05"
                                value={threshold}
                                aria-label="Review threshold"
                                onChange={(event) =>
                                    sim.setThreshold(Number(event.target.value))
                                }
                            />
                            <dl className="m">
                                <div>
                                    <dt>Flagged</dt>
                                    <dd>
                                        {snapshot.delivered
                                            ? `${snapshot.flaggedPercent}%`
                                            : "–"}
                                    </dd>
                                </div>
                                <div>
                                    <dt>Precision</dt>
                                    <dd>{precision}</dd>
                                </div>
                                <div>
                                    <dt>Recall</dt>
                                    <dd>{recall}</dd>
                                </div>
                                <div>
                                    <dt>Risky</dt>
                                    <dd>{snapshot.risky}</dd>
                                </div>
                            </dl>
                            <p className="tiny">
                                Risky means a generated scenario, not verified
                                fraud. 0.50 is only a demo default; real
                                thresholds depend on review capacity.
                            </p>
                        </div>
                    </div>
                    <DecisionFeed
                        records={snapshot.feed}
                        isReview={sim.isReview}
                        reason={sim.reason}
                    />
                </div>
            </div>
            <p className="fine">
                This simulator runs in your browser and follows
                MeshShield&apos;s ideas: integrity checks first, point-in-time
                features, then a logistic-style score. The weights are
                illustrative. The real model is trained in Python on a
                chronological split.
            </p>
        </div>
    );
}
