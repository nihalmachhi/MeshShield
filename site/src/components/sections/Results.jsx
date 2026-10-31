import { results } from "../../data/results.js";

function Bar({ value, color }) {
    return (
        <span className="tr">
            <i
                style={{
                    width: `${Math.max(2, value * 100)}%`,
                    background: color,
                }}
            />
        </span>
    );
}

function ModelCard({ title, description, values, color }) {
    const max = Math.max(...Object.values(values));
    return (
        <article className="card">
            <h3>{title}</h3>
            <p>{description}</p>
            <div className="viz">
                <div className="mrow">
                    <span>Precision</span>
                    <Bar value={values.precision} color={color} />
                    <b>{values.precision.toFixed(2)}</b>
                </div>
                <div className="mrow">
                    <span>Recall</span>
                    <Bar value={values.recall} color={color} />
                    <b>{values.recall.toFixed(2)}</b>
                </div>
                <div className="mrow">
                    <span>F1</span>
                    <Bar value={values.f1} color={color} />
                    <b>{values.f1.toFixed(2)}</b>
                </div>
                <div className="mrow">
                    <span>Avg prec.</span>
                    <Bar value={values.prAuc} color={color} />
                    <b>{values.prAuc.toFixed(3)}</b>
                </div>
            </div>
        </article>
    );
}

export default function Results() {
    const { dataset, models } = results;

    return (
        <section className="sec wrap" id="results">
            <div className="center">
                <h2>
                    Measured on a later{" "}
                    <span className="d2">
                        slice of{" "}
                        <i className="tile c-c">
                            <svg viewBox="0 0 24 24" aria-hidden="true">
                                <path d="M5 20V10M12 20V4M19 20v-7" />
                            </svg>
                        </i>{" "}
                        time.
                    </span>
                </h2>
                <p className="lede">
                    The models train on the earliest 80% of events and are
                    tested on the latest 20%: {dataset.test} payments,{" "}
                    {dataset.positives} of them risky scenarios. Figures from
                    the saved run:
                </p>
            </div>
            <div className="cards">
                <ModelCard
                    title="Graph features"
                    description="Logistic regression with device-graph features added."
                    values={models.graph}
                    color="var(--c-purple)"
                />
                <ModelCard
                    title="Transaction only"
                    description="The same model without graph features."
                    values={models.nonGraph}
                    color="var(--c-yellow)"
                />
                <ModelCard
                    title="Rules only"
                    description="Simple fixed rules, no learned model."
                    values={models.rules}
                    color="var(--c-red)"
                />
            </div>
            <p
                className="fine center"
                style={{ maxWidth: "72ch", margin: "18px auto 0" }}
            >
                Honest reading: on this run the graph features beat the
                transaction-only model on average precision (0.678 vs 0.545),
                with a paired bootstrap interval for the difference of +0.064 to
                +0.216 that excludes zero. They do not beat fixed rules on
                PR-AUC. The test set is small and the labels are generated
                scenarios, not verified fraud. The full pipeline, which adds
                integrity checks, has the best PR-AUC of the learned models
                (0.859). The Brier score is reported but does not claim the
                model is calibrated.
            </p>
        </section>
    );
}
