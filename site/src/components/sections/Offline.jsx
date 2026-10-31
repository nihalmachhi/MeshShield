import { scrollToId } from "../../lib/dom.js";

const DELIVERY_RUN = {
    delivered: 1695,
    accepted: 1487,
    duplicates: 108,
    rejected: 100,
};

const acceptedPercent = Math.round(
    (DELIVERY_RUN.accepted / DELIVERY_RUN.delivered) * 100,
);

export default function Offline({ sim }) {
    return (
        <section className="sec wrap" id="offline">
            <div className="split">
                <div>
                    <h2>
                        When sync arrives late,{" "}
                        <span className="d2">
                            nothing{" "}
                            <i className="tile c-y">
                                <svg viewBox="0 0 24 24" aria-hidden="true">
                                    <circle cx="12" cy="12" r="8" />
                                    <path d="M12 8v4l3 2" />
                                </svg>
                            </i>{" "}
                            breaks.
                        </span>
                    </h2>
                    <p className="lede">
                        Payments queue offline and arrive late, out of order or
                        twice. Event time and ingestion time stay separate, so a
                        delay never leaks into history.
                    </p>
                    <dl className="facts">
                        <div>
                            <dt>Two clocks</dt>
                            <dd>
                                event_time is when the payment was created.
                                ingestion_time is when its sync was received.
                            </dd>
                        </div>
                        <div>
                            <dt>Idempotency</dt>
                            <dd>
                                SQLite stores each event ID once. A retried
                                delivery is ignored, not applied twice.
                            </dd>
                        </div>
                        <div>
                            <dt>Delivery run</dt>
                            <dd>
                                {DELIVERY_RUN.delivered} deliveries:{" "}
                                {DELIVERY_RUN.accepted} accepted,{" "}
                                {DELIVERY_RUN.duplicates} duplicates ignored,{" "}
                                {DELIVERY_RUN.rejected} invalid signatures
                                rejected.
                            </dd>
                        </div>
                        <div>
                            <dt>Replay demo</dt>
                            <dd>
                                POST /api/replay applies the same sync event
                                twice to show the second is refused.
                            </dd>
                        </div>
                    </dl>
                </div>
                <div className="stage" style={{ marginTop: 0 }}>
                    <div
                        className="ui"
                        style={{ padding: 16, display: "grid", gap: 12 }}
                    >
                        <div className="feed">
                            <h3>Arrival order · example</h3>
                            <ul className="tl">
                                <li>
                                    <span>txn_0412</span>
                                    <span className="o">event 09:02</span>
                                    <span>arrives 09:04</span>
                                </li>
                                <li>
                                    <span>txn_0414</span>
                                    <span className="o">event 09:05</span>
                                    <span>arrives 09:06</span>
                                </li>
                                <li>
                                    <span>txn_0413</span>
                                    <span className="o">event 09:03</span>
                                    <span className="late">arrives 09:51</span>
                                </li>
                            </ul>
                            <p className="tiny" style={{ marginTop: 8 }}>
                                txn_0413 arrives last but happened second.
                                Features for it use only events before 09:03.
                            </p>
                        </div>
                        <div className="feed">
                            <h3>Replay demo</h3>
                            <div className="term" id="rp">
                                <span className="q">
                                    Press the button to deliver one event twice.
                                </span>
                            </div>
                            <div style={{ marginTop: 10 }}>
                                <button
                                    className="ab pri"
                                    type="button"
                                    onClick={() => sim.step("replay")}
                                >
                                    Deliver the same event twice
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <p
                className="fine center"
                style={{ maxWidth: "72ch", margin: "18px auto 0" }}
            >
                Two clocks, one event-time history, an idempotent queue. Of the
                recorded run, {acceptedPercent}% of deliveries were accepted;
                the rest are counted as duplicates or invalid signatures.
            </p>
            <p className="center" style={{ marginTop: 14 }}>
                <button
                    className="link"
                    type="button"
                    onClick={() => scrollToId("demo")}
                >
                    Open the simulator →
                </button>
            </p>
        </section>
    );
}
