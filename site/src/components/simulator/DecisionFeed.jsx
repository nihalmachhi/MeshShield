import { clock } from "../../lib/simulation.js";

export default function DecisionFeed({ records, isReview, reason }) {
    return (
        <div className="feed">
            <h3>Decision feed</h3>
            <ol>
                {records.map((record) => {
                    const review = isReview(record);
                    const late = record.arrival - record.event.time;
                    return (
                        <li
                            key={`${record.sequence}-${record.event.transaction}`}
                        >
                            <span className="t">{clock(record.arrival)}</span>
                            <span className="to">
                                {record.event.transaction}
                            </span>
                            <span className="sm">
                                ${record.event.amount.toFixed(2)} ·{" "}
                                {record.event.account} · {record.event.device}
                            </span>
                            <span className={`st ${review ? "s5" : "s2"}`}>
                                {review ? "review" : "low risk"}
                            </span>
                            <span className="r">
                                {record.outcome} · event{" "}
                                {clock(record.event.time)}, arrived{" "}
                                {clock(record.arrival)}
                                {late >= 30 ? ` (${late} min late)` : ""} · risk{" "}
                                {Math.round(record.probability * 100)}% ·{" "}
                                {reason(record)}
                            </span>
                        </li>
                    );
                })}
            </ol>
        </div>
    );
}
