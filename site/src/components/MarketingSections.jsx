export default function MarketingSections() {
    return (
        <>
            <section id="how" className="section">
                <div className="section-intro center">
                    <p className="eyebrow">A clear event trail</p>
                    <h2>Three steps. One payment trail.</h2>
                    <p className="lede">
                        The project separates delivery integrity from model risk
                        so a reviewer can see what happened and why.
                    </p>
                </div>
                <div className="step-grid">
                    {[
                        [
                            "01",
                            "Generate",
                            "Create reproducible synthetic offline payments and delayed sync events.",
                        ],
                        [
                            "02",
                            "Check integrity",
                            "Reject invalid signatures and ignore duplicate event IDs during sync.",
                        ],
                        [
                            "03",
                            "Score risk",
                            "Build features from earlier event-time history and compare model signals with rules.",
                        ],
                    ].map(([number, title, text]) => (
                        <article key={number} className="step-card">
                            <span className="step-number">{number}</span>
                            <h3>{title}</h3>
                            <p>{text}</p>
                        </article>
                    ))}
                </div>
            </section>

            <section className="split-section">
                <div>
                    <p className="eyebrow">Built for inspection</p>
                    <h2>Every flag comes with evidence.</h2>
                    <p className="lede">
                        Review the event context, integrity findings, risk
                        score, and the top model contributions together. The
                        result is a reason to investigate, not a claim about
                        causality.
                    </p>
                    <div className="fact-list">
                        <div>
                            <b>Event time</b>
                            <span>
                                History is ordered by when the payment happened.
                            </span>
                        </div>
                        <div>
                            <b>Ingestion time</b>
                            <span>
                                Sync arrival is recorded separately, including
                                late delivery.
                            </span>
                        </div>
                        <div>
                            <b>Human review</b>
                            <span>
                                A reviewer stays responsible for every follow-up
                                decision.
                            </span>
                        </div>
                    </div>
                </div>
                <aside className="quote-card">
                    <span className="quote-mark">“</span>
                    <blockquote>
                        When sync arrives late, nothing breaks.
                    </blockquote>
                    <p>
                        Duplicate events remain idempotent; integrity failures
                        stay visible in the review trail.
                    </p>
                    <div className="mini-timeline">
                        <span>offline payment</span>
                        <i /> <span>delayed sync</span>
                        <i /> <span>review evidence</span>
                    </div>
                </aside>
            </section>

            <section id="results" className="section results-section">
                <div className="section-intro center">
                    <p className="eyebrow">Synthetic holdout results</p>
                    <h2>Measured on a later slice of time.</h2>
                    <p className="lede">
                        Run <code>meshshield demo</code> to generate a
                        reproducible event-time evaluation. Reported
                        measurements describe the synthetic generator only.
                    </p>
                </div>
                <div className="result-grid">
                    {[
                        [
                            "Graph features",
                            "Relationship signals add velocity and shared-device history.",
                        ],
                        [
                            "Transaction baseline",
                            "A simple comparison using transaction-only features.",
                        ],
                        [
                            "Rules only",
                            "Transparent conditions provide a non-model baseline.",
                        ],
                        [
                            "Calibrated scores",
                            "Calibration is evaluated on a separate chronological slice.",
                        ],
                    ].map(([title, text]) => (
                        <article key={title} className="result-card">
                            <span className="result-icon">↗</span>
                            <h3>{title}</h3>
                            <p>{text}</p>
                        </article>
                    ))}
                </div>
                <p className="result-caveat">
                    Synthetic labels encode scenarios from the generator; these
                    results are not evidence of real-world fraud performance.
                </p>
            </section>

            <section id="quick-start" className="section quick-start">
                <div className="section-intro">
                    <p className="eyebrow">Run it locally</p>
                    <h2>A reproducible demo, start to finish.</h2>
                    <p className="lede">
                        Python runs the research pipeline and API. Node.js
                        builds the React interface.
                    </p>
                </div>
                <div className="quick-grid">
                    <div className="quick-steps">
                        {[
                            [
                                "1",
                                "Create an environment",
                                "python -m venv .venv",
                            ],
                            [
                                "2",
                                "Install and build the interface",
                                "python -m pip install -e .  ·  cd site && npm install && npm run build",
                            ],
                            [
                                "3",
                                "Run the demo",
                                "meshshield demo  ·  meshshield serve",
                            ],
                        ].map(([number, title, command]) => (
                            <article key={number}>
                                <span>{number}</span>
                                <div>
                                    <h3>{title}</h3>
                                    <code>{command}</code>
                                </div>
                            </article>
                        ))}
                    </div>
                    <div className="quick-note">
                        <h3>What you need</h3>
                        <p>
                            Python 3.11+ and Node.js 20+. The interface is built
                            into <code>site/dist</code> and served by the local
                            API.
                        </p>
                        <a href="https://github.com/nihalmachhi/MeshShield">
                            Browse source on GitHub ↗
                        </a>
                    </div>
                </div>
            </section>

            <footer>
                <a className="brand" href="#top">
                    <span className="brand-icon">M</span> MeshShield
                </a>
                <p>Offline payment risk research · synthetic data only</p>
                <a href="https://github.com/nihalmachhi/MeshShield">GitHub ↗</a>
            </footer>
        </>
    );
}
