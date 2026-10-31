import { scrollToId } from "../../lib/dom.js";

export default function Pipeline({ sim }) {
    return (
        <section className="sec wrap" id="pipeline">
            <div className="center">
                <h2>
                    Three steps.{" "}
                    <span className="d2">
                        One{" "}
                        <i className="tile c-g">
                            <svg viewBox="0 0 24 24" aria-hidden="true">
                                <path d="M5 12.5l4.5 4.5L19 7" />
                            </svg>
                        </i>{" "}
                        payment trail.
                    </span>
                </h2>
                <p className="lede">
                    Every transaction is generated, checked and scored in order,
                    using only what was known when it happened.
                </p>
            </div>
            <div className="cards">
                <article className="card">
                    <span className="ic c-p">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M4 7h16M4 12h16M4 17h16" />
                        </svg>
                    </span>
                    <h3>1. Generate</h3>
                    <p>
                        A seeded generator creates synthetic payments with an
                        event time and an arrival time, then delays, duplicates
                        and reorders the sync.
                    </p>
                    <div className="viz">
                        <div className="chips">
                            <span>normal 84%</span>
                            <span>high amount</span>
                            <span>shared device</span>
                            <span>replay</span>
                            <span>bad signature</span>
                        </div>
                        <div className="leg">1,600 payments · seed 2025</div>
                    </div>
                    <button
                        className="link"
                        type="button"
                        onClick={() => scrollToId("demo")}
                    >
                        Watch it in the simulator →
                    </button>
                </article>
                <article className="card">
                    <span className="ic c-y">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z" />
                        </svg>
                    </span>
                    <h3>2. Check integrity</h3>
                    <p>
                        Hard rules run first and stay apart from the model:
                        duplicate event IDs, replayed events and invalid
                        signatures.
                    </p>
                    <div className="viz">
                        <div className="hd" aria-hidden="true">
                            <i />
                            <i />
                            <i className="x" />
                            <i />
                        </div>
                        <div className="leg">
                            SQLite accepts each event ID once
                        </div>
                    </div>
                    <button
                        className="link"
                        type="button"
                        onClick={() => sim.force("bad signature")}
                    >
                        Send a bad signature →
                    </button>
                </article>
                <article className="card">
                    <span className="ic c-o">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M5 20V10M12 20V4M19 20v-7" />
                        </svg>
                    </span>
                    <h3>3. Score risk</h3>
                    <p>
                        Features come from earlier history only. A standardized
                        logistic regression returns a risk score and the inputs
                        that pushed it up.
                    </p>
                    <div className="viz">
                        <div
                            className="wt"
                            role="img"
                            aria-label="Feature groups: transaction, velocity, graph"
                        >
                            <span className="a">amount, time</span>
                            <span className="b">velocity</span>
                            <span className="c">graph</span>
                        </div>
                        <div className="leg">
                            16 features, 7 from the device graph
                        </div>
                    </div>
                    <button
                        className="link"
                        type="button"
                        onClick={() => scrollToId("evidence")}
                    >
                        See the evidence →
                    </button>
                </article>
            </div>
        </section>
    );
}
