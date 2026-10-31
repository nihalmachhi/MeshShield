import { clock } from "../../lib/simulation.js";

export default function Inspector({ sim }) {
    const { selected, selectedReview, threshold } = sim.snapshot;

    if (!selected) {
        return <div className="ui insp" id="insp" aria-live="off" />;
    }

    const features = [...selected.features].sort(
        (left, right) =>
            Math.abs(right.contribution) - Math.abs(left.contribution),
    );
    const largest = Math.max(
        0.5,
        ...features.map((item) => Math.abs(item.contribution)),
    );
    const why = selected.findings.length
        ? "An integrity finding on its own sends this payment to review. The model score is listed separately."
        : selected.probability >= threshold
          ? "No integrity finding. The model score is at or above the threshold."
          : "No integrity finding. The model score is below the threshold.";

    return (
        <div className="ui insp" id="insp" aria-live="off">
            <div className="ib">
                <span className={`pill ${selectedReview ? "bad" : "ok"}`}>
                    {selectedReview ? "review" : "low risk"}
                </span>
                <b className="mono">{selected.event.transaction}</b>
                <span className="pol">
                    risk {(selected.probability * 100).toFixed(1)}% · threshold{" "}
                    {threshold.toFixed(2)}
                </span>
            </div>
            <p className="why">
                {why} Features use only events before{" "}
                {clock(selected.event.time)}.
            </p>
            <div className="sh">Integrity findings</div>
            <ul className="irs">
                {selected.findings.length ? (
                    selected.findings.map((finding) => (
                        <li className="ir hit" key={finding}>
                            <div className="irh">
                                <span>{finding}</span>
                                <span>{selected.outcome}</span>
                            </div>
                            <div className="irm">
                                Hard check, not a model estimate
                            </div>
                        </li>
                    ))
                ) : (
                    <li className="ir none">
                        <div className="irh">
                            <span>None</span>
                            <span>passed</span>
                        </div>
                        <div className="irm">Signature valid, event ID new</div>
                    </li>
                )}
            </ul>
            <div className="sh">Model contributions</div>
            <ul className="irs">
                {features.map((feature) => (
                    <li className="ir" key={feature.name}>
                        <div className="irh">
                            <span>{feature.name}</span>
                            <span>
                                {feature.contribution >= 0 ? "+" : ""}
                                {feature.contribution.toFixed(2)}
                            </span>
                        </div>
                        <span className="bar">
                            <i
                                className={
                                    feature.contribution > 0 ? "up" : "dn"
                                }
                                style={{
                                    width: `${Math.max(
                                        3,
                                        (Math.abs(feature.contribution) /
                                            largest) *
                                            100,
                                    )}%`,
                                }}
                            />
                        </span>
                        <div className="irm">
                            {feature.value} ·{" "}
                            {feature.contribution > 0
                                ? "pushes the score up"
                                : feature.contribution < 0
                                  ? "pushes the score down"
                                  : "no effect"}
                        </div>
                    </li>
                ))}
            </ul>
            {sim.snapshot.pinned ? (
                <div className="foot-ab">
                    <button className="ab" type="button" onClick={sim.follow}>
                        Follow live traffic
                    </button>
                </div>
            ) : null}
        </div>
    );
}
