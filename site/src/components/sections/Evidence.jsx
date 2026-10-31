import { scrollToId } from "../../lib/dom.js";
import Inspector from "../simulator/Inspector.jsx";

export default function Evidence({ sim }) {
    const { snapshot } = sim;

    return (
        <section className="sec wrap" id="evidence">
            <div className="split">
                <div className="stage" style={{ marginTop: 0 }}>
                    <Inspector sim={sim} />
                </div>
                <div>
                    <h2>
                        Every flag comes{" "}
                        <span className="d2">
                            with{" "}
                            <i className="tile c-r">
                                <svg viewBox="0 0 24 24" aria-hidden="true">
                                    <circle cx="11" cy="11" r="6" />
                                    <path d="M20 20l-4.5-4.5" />
                                </svg>
                            </i>{" "}
                            evidence.
                        </span>
                    </h2>
                    <p className="lede">
                        MeshShield keeps two kinds of evidence apart. This panel
                        follows the latest payment, or the one you pick below.
                    </p>
                    <dl className="facts">
                        <div>
                            <dt>Integrity findings</dt>
                            <dd>
                                Direct checks such as a failed signature or a
                                repeated event ID. They can send a payment to
                                review on their own.
                            </dd>
                        </div>
                        <div>
                            <dt>Model contributions</dt>
                            <dd>
                                Associations learned from training data. They
                                show what moved the score, not what caused
                                fraud.
                            </dd>
                        </div>
                        <div>
                            <dt>Point-in-time</dt>
                            <dd>
                                Velocity and device counts use earlier event
                                times only. The current payment joins history
                                after its features are recorded.
                            </dd>
                        </div>
                    </dl>
                    <div className="codes">
                        <button
                            className="btn btn-dark btn-sm"
                            type="button"
                            onClick={() => sim.force("shared device")}
                        >
                            Inspect a shared device
                        </button>
                        <button
                            className="btn btn-ghost btn-sm"
                            type="button"
                            onClick={() => sim.force("bad signature")}
                        >
                            Inspect a bad signature
                        </button>
                        <button
                            className="btn btn-ghost btn-sm"
                            type="button"
                            onClick={() => sim.force("replay")}
                        >
                            Inspect a replay
                        </button>
                        <button
                            className="btn btn-ghost btn-sm"
                            type="button"
                            onClick={() => sim.force("high amount")}
                        >
                            Inspect a high amount
                        </button>
                    </div>
                </div>
            </div>
        </section>
    );
}
