export default function Scope() {
    return (
        <section className="sec wrap">
            <div className="center">
                <h2>
                    Built to{" "}
                    <span className="d2">
                        <i className="tile c-o">
                            <svg viewBox="0 0 24 24" aria-hidden="true">
                                <path d="M9 18h6M10 21h4M12 3a6 6 0 00-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0012 3z" />
                            </svg>
                        </i>{" "}
                        teach.
                    </span>
                </h2>
                <p className="lede">
                    MeshShield is for learning how offline payment risk review
                    works. It is not for moving money.
                </p>
            </div>
            <div className="two">
                <div className="card">
                    <span className="ic c-g">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M5 12.5l4.5 4.5L19 7" />
                        </svg>
                    </span>
                    <h3>In scope</h3>
                    <ul>
                        <li>Seeded synthetic payments and a dataset card</li>
                        <li>Signature, duplicate and replay checks</li>
                        <li>Leak-free chronological evaluation</li>
                        <li>Logistic baseline vs graph features vs rules</li>
                        <li>A local dashboard and JSON API</li>
                    </ul>
                </div>
                <div className="card">
                    <span className="ic c-r">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg>
                    </span>
                    <h3>Out of scope</h3>
                    <ul>
                        <li>Authorizing or settling real payments</li>
                        <li>Real fraud labels or real customer data</li>
                        <li>Network-facing deployment</li>
                        <li>Real cryptographic signatures, for now</li>
                        <li>Claims about real-world accuracy</li>
                    </ul>
                </div>
            </div>
        </section>
    );
}
