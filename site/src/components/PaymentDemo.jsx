export default function PaymentDemo({
    mode,
    setMode,
    modes,
    payments,
    sendPayment,
    runBatch,
    onReset,
    accepted,
    duplicates,
    rejected,
    reviewCount,
    selected,
    setSelected,
}) {
    return (
        <section id="demo" className="demo-section">
            <div className="demo-heading">
                <div>
                    <p className="eyebrow">Interactive demo</p>
                    <h2>Replay the payment trail.</h2>
                </div>
                <p>
                    Change the scenario, send events, and inspect why one is
                    routed for review.
                </p>
            </div>
            <div className="simulator">
                <div className="sim-header">
                    <div className="sim-brand">
                        <span className="pulse" />{" "}
                        <strong>MeshShield risk lab</strong>
                        <span className="muted">synthetic event stream</span>
                    </div>
                    <div className="stat-row">
                        <span>
                            <b>{payments.length}</b> delivered
                        </span>
                        <span>
                            <b>{accepted}</b> accepted
                        </span>
                        <span>
                            <b>{reviewCount}</b> flagged
                        </span>
                    </div>
                </div>
                <div className="controls">
                    <div
                        className="mode-list"
                        role="group"
                        aria-label="Select a simulated payment pattern"
                    >
                        {modes.map((item) => (
                            <button
                                type="button"
                                key={item}
                                className={mode === item ? "active" : ""}
                                aria-pressed={mode === item}
                                onClick={() => setMode(item)}
                            >
                                {item}
                            </button>
                        ))}
                    </div>
                    <div className="control-actions">
                        <button type="button" onClick={() => sendPayment()}>
                            Send payment
                        </button>
                        <button type="button" onClick={runBatch}>
                            Run 8
                        </button>
                        <button
                            type="button"
                            onClick={() => {
                                setPayments([]);
                                setSelected(null);
                                sequence.current = 0;
                            }}
                        >
                            Reset
                        </button>
                    </div>
                </div>
                <div className="sim-grid">
                    <div className="sim-column">
                        <section className="sim-card">
                            <div className="card-head">
                                <h3>Sync queue</h3>
                                <span className="muted">integrity checks</span>
                            </div>
                            <div className="queue-bar">
                                <span
                                    style={{
                                        width: `${payments.length ? (accepted / payments.length) * 100 : 0}%`,
                                    }}
                                />
                            </div>
                            <div className="queue-stats">
                                <span>
                                    <b>{accepted}</b> accepted
                                </span>
                                <span>
                                    <b>{duplicates}</b> duplicates
                                </span>
                                <span>
                                    <b>{rejected}</b> rejected
                                </span>
                            </div>
                        </section>
                        <section className="sim-card">
                            <div className="card-head">
                                <h3>Device links</h3>
                                <span
                                    className={`tag ${payments.some((payment) => payment.scenario === "shared device") ? "warn" : "ok"}`}
                                >
                                    {payments.some(
                                        (payment) =>
                                            payment.scenario ===
                                            "shared device",
                                    )
                                        ? "shared device"
                                        : "watching"}
                                </span>
                            </div>
                            <div className="device-list">
                                {payments.slice(0, 4).map((payment) => (
                                    <button
                                        key={payment.id}
                                        onClick={() => setSelected(payment)}
                                    >
                                        <span className="node" />
                                        <b>{payment.device}</b>
                                        <small>{payment.account}</small>
                                    </button>
                                ))}
                            </div>
                            {!payments.length && (
                                <p className="muted">
                                    Device and account links appear as payments
                                    arrive.
                                </p>
                            )}
                        </section>
                        <section className="sim-card feed-card">
                            <div className="card-head">
                                <h3>Decision feed</h3>
                                <span className="muted">latest events</span>
                            </div>
                            {payments.length ? (
                                <ol className="feed">
                                    {payments.slice(0, 5).map((payment) => (
                                        <li
                                            key={payment.id}
                                            onClick={() => setSelected(payment)}
                                        >
                                            <div className="feed-top">
                                                <time>{payment.time}</time>
                                                <b>{payment.id}</b>
                                                <span
                                                    className={`tag ${payment.review ? "warn" : "ok"}`}
                                                >
                                                    {payment.review
                                                        ? "review"
                                                        : "clear"}
                                                </span>
                                            </div>
                                            <p>{`$${payment.amount.toFixed(2)} · ${payment.account} · ${payment.device}`}</p>
                                        </li>
                                    ))}
                                </ol>
                            ) : (
                                <p className="muted">
                                    Waiting for the first simulated event…
                                </p>
                            )}
                        </section>
                    </div>
                    <section className="sim-card evidence-card">
                        <div className="card-head">
                            <h3>Selected evidence</h3>
                            {selected && (
                                <span
                                    className={`tag ${selected.review ? "warn" : "ok"}`}
                                >
                                    {selected.review ? "review" : "low risk"}
                                </span>
                            )}
                        </div>
                        {selected ? (
                            <>
                                <div className="evidence-title">
                                    <b>{selected.id}</b>
                                    <span>
                                        {(selected.risk * 100).toFixed(1)}% risk
                                    </span>
                                </div>
                                <p className="muted">
                                    {!selected.signatureValid
                                        ? "Invalid signature. Integrity checks route this event for review."
                                        : selected.duplicate
                                          ? "Duplicate event ID detected. The repeated event is ignored and flagged for review."
                                          : "Integrity checks passed. The illustrative score determines whether this event is queued for review."}
                                </p>
                                <ul className="factor-list">
                                    {selected.factors.map(([name, value]) => (
                                        <li key={name}>
                                            <span>{name}</span>
                                            <b>
                                                {value >= 0 ? "+" : ""}
                                                {value.toFixed(2)}
                                            </b>
                                            <small>
                                                {value >= 0
                                                    ? "raises score"
                                                    : "lowers score"}
                                            </small>
                                        </li>
                                    ))}
                                </ul>
                            </>
                        ) : (
                            <p className="muted empty-evidence">
                                Send a payment to inspect its evidence.
                            </p>
                        )}
                    </section>
                </div>
                <p className="sim-foot">
                    Illustrative simulator. Events and scores are generated in
                    your browser and do not call the Python API.
                </p>
            </div>
        </section>
    );
}
