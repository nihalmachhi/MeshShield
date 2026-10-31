export default function Features() {
    return (
        <section className="sec wrap" id="features">
            <div className="center">
                <h2>
                    A small system.{" "}
                    <span className="d2">
                        Built to be{" "}
                        <i className="tile c-p">
                            <svg viewBox="0 0 24 24" aria-hidden="true">
                                <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z" />
                                <path d="M12 12l8-4.5M12 12v9M12 12L4 7.5" />
                            </svg>
                        </i>{" "}
                        inspected.
                    </span>
                </h2>
                <p className="lede">
                    Data contracts, generation, features, model, evaluation,
                    sync, persistence, CLI and web UI each live in their own
                    module.
                </p>
            </div>
            <div className="bento">
                <article className="bc s2">
                    <span className="ic c-p">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <circle cx="12" cy="12" r="8" />
                            <path d="M12 8v4l3 2" />
                        </svg>
                    </span>
                    <h3>Time-aware features</h3>
                    <p>
                        Account and merchant velocity, device reuse,
                        delayed-sync duration, time of day and past transaction
                        counts, plus causal graph structure.
                    </p>
                    <div className="bv">
                        <div className="bvi">
                            <div className="spark" aria-hidden="true">
                                <i style={{ height: "35%" }} />
                                <i style={{ height: "55%" }} />
                                <i style={{ height: "42%" }} />
                                <i style={{ height: "70%" }} />
                                <i style={{ height: "48%" }} />
                                <i style={{ height: "80%" }} />
                                <i style={{ height: "60%" }} />
                                <i style={{ height: "38%" }} />
                            </div>
                        </div>
                    </div>
                </article>
                <article className="bc s2">
                    <span className="ic c-o">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M9 7l-5 5 5 5M15 7l5 5-5 5" />
                        </svg>
                    </span>
                    <h3>Local JSON API</h3>
                    <p>
                        Health, metrics, scored transactions, ablation,
                        calibration, drift and the replay demo. Bound to
                        127.0.0.1 with no authentication, so keep it local.
                    </p>
                    <div className="bv">
                        <div className="bvi term">
                            <b>GET</b> /api/health
                            <br />
                            <b>GET</b> /api/metrics
                            <br />
                            <b>GET</b> /api/transactions?limit=100
                            <br />
                            <b>GET</b> /api/ablation
                            <br />
                            <b>GET</b> /api/calibration
                            <br />
                            <b>GET</b> /api/drift
                            <br />
                            <b>POST</b> /api/replay
                        </div>
                    </div>
                </article>
                <article className="bc">
                    <span className="ic c-g">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M5 12.5l4.5 4.5L19 7" />
                        </svg>
                    </span>
                    <h3>Reproducible</h3>
                    <p>
                        A fixed seed and a dataset card record where the data
                        came from.
                    </p>
                    <div className="bv">
                        <div className="chips">
                            <span>seed 2025</span>
                        </div>
                    </div>
                </article>
                <article className="bc">
                    <span className="ic c-y">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <circle cx="11" cy="11" r="6" />
                            <path d="M20 20l-4.5-4.5" />
                        </svg>
                    </span>
                    <h3>Auditable</h3>
                    <p>Hard findings and model evidence never mix.</p>
                    <div className="bv">
                        <div className="chips">
                            <span>findings</span>
                            <span>contributions</span>
                        </div>
                    </div>
                </article>
                <article className="bc s2">
                    <span className="ic c-r">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M5 20V10M12 20V4M19 20v-7" />
                        </svg>
                    </span>
                    <h3>Metrics that fit imbalance</h3>
                    <p>
                        Precision, recall, F1, average precision, ROC-AUC, Brier
                        score, confusion counts, reliability bins and paired
                        bootstrap intervals, on a chronological holdout.
                    </p>
                    <div className="bv">
                        <div className="bvi">
                            <div className="chips">
                                <span>precision</span>
                                <span>recall</span>
                                <span>F1</span>
                                <span>avg precision</span>
                                <span>ROC-AUC</span>
                                <span>Brier</span>
                                <span>bootstrap</span>
                                <span>confusion</span>
                            </div>
                        </div>
                    </div>
                </article>
                <article className="bc s2">
                    <span className="ic c-pk">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M7 4h7l4 4v12H7zM14 4v4h4" />
                        </svg>
                    </span>
                    <h3>SQLite idempotency</h3>
                    <p>
                        A durable table accepts each event ID once, without
                        PostgreSQL, Redis, queues or cloud accounts.
                    </p>
                    <div className="bv">
                        <div className="bvi term">
                            <b>evt_0412</b>{" "}
                            <span className="q">→ accepted</span>
                            <br />
                            <b>evt_0412</b>{" "}
                            <span className="q">→ duplicate, ignored</span>
                        </div>
                    </div>
                </article>
                <article className="bc">
                    <span className="ic c-k">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M9 7l-5 5 5 5M15 7l5 5-5 5" />
                        </svg>
                    </span>
                    <h3>Standard library</h3>
                    <p>No runtime packages to install.</p>
                    <div className="bv">
                        <div className="chips">
                            <span>Python 3.11+</span>
                        </div>
                    </div>
                </article>
                <article className="bc">
                    <span className="ic c-c">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M7 4h7l4 4v12H7zM14 4v4h4" />
                        </svg>
                    </span>
                    <h3>JSONL data</h3>
                    <p>Inspectable transactions and sync events.</p>
                    <div className="bv">
                        <div className="chips">
                            <span>data/generated</span>
                        </div>
                    </div>
                </article>
                <article className="bc s4">
                    <span className="ic c-g">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M5 12h14M13 6l6 6-6 6" />
                        </svg>
                    </span>
                    <h3>Not in this release</h3>
                    <p>
                        Graph neural networks, real cryptography, CRDT sync,
                        federated learning, per-feature attribution and
                        public-data training remain out of scope.
                    </p>
                    <div className="bv">
                        <div className="bvi">
                            <div className="chips">
                                <span>GNN</span>
                                <span>real Ed25519 signatures</span>
                                <span>CRDT sync</span>
                                <span>federated learning</span>
                                <span>per-feature attribution</span>
                                <span>public-data training</span>
                            </div>
                        </div>
                    </div>
                </article>
            </div>
        </section>
    );
}
