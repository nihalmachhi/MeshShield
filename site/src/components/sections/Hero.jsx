import Simulator from "../simulator/Simulator.jsx";
import { REPO } from "../layout/Header.jsx";

export default function Hero({ sim }) {
    return (
        <section className="hero wrap" id="top">
            <h1>
                Catch risky offline payments <span className="g">before</span>{" "}
                they sync. <span className="d">And show the evidence.</span>
            </h1>
            <p className="sub">
                MeshShield is a local research simulator for an offline payment
                network. It generates delayed, duplicate and tampered payments,
                checks their integrity, builds time-aware features and scores
                risk, then shows the evidence behind every flag.
            </p>
            <div className="cta">
                <a className="btn btn-dark" href={REPO}>
                    View on GitHub
                </a>
                <a className="btn btn-ghost" href="#start">
                    Run it locally
                </a>
            </div>
            <p className="note">
                Python standard library only. A synthetic research prototype
                that never moves money.
            </p>
            <Simulator sim={sim} />
        </section>
    );
}
