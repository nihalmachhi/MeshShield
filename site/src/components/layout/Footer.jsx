import Wordmark from "./Wordmark.jsx";
import { REPO } from "./Header.jsx";

export default function Footer() {
    return (
        <footer className="foot">
            <div className="wrap">
                <div className="foot-panel">
                    <div className="foot-top">
                        <div>
                            <a className="brand" href="#top">
                                <span className="logo" aria-hidden="true" />
                                MeshShield
                            </a>
                            <p>
                                A local, synthetic simulator for risk review in
                                an offline payment network.
                            </p>
                        </div>
                        <nav aria-label="Product">
                            <h4>Product</h4>
                            <ul>
                                <li>
                                    <a href="#demo">Simulator</a>
                                </li>
                                <li>
                                    <a href="#pipeline">Pipeline</a>
                                </li>
                                <li>
                                    <a href="#evidence">Evidence</a>
                                </li>
                                <li>
                                    <a href="#offline">Offline sync</a>
                                </li>
                                <li>
                                    <a href="#results">Results</a>
                                </li>
                            </ul>
                        </nav>
                        <nav aria-label="Run it">
                            <h4>Run it</h4>
                            <ul>
                                <li>
                                    <a href="#features">Features</a>
                                </li>
                                <li>
                                    <a href="#start">Quick start</a>
                                </li>
                                <li>
                                    <a href="#faq">FAQ</a>
                                </li>
                            </ul>
                        </nav>
                        <nav aria-label="Source">
                            <h4>Source</h4>
                            <ul>
                                <li>
                                    <a href={REPO}>GitHub</a>
                                </li>
                                <li>
                                    <a
                                        href={`${REPO}/blob/main/docs/system-model.md`}
                                    >
                                        System model
                                    </a>
                                </li>
                                <li>
                                    <a
                                        href={`${REPO}/blob/main/docs/feature-contract.md`}
                                    >
                                        Feature contract
                                    </a>
                                </li>
                                <li>
                                    <a
                                        href={`${REPO}/blob/main/docs/threat-model.md`}
                                    >
                                        Threat model
                                    </a>
                                </li>
                                <li>
                                    <a
                                        href={`${REPO}/blob/main/docs/evaluation.md`}
                                    >
                                        Evaluation
                                    </a>
                                </li>
                            </ul>
                        </nav>
                    </div>
                    <div className="foot-fine">
                        <span>
                            Synthetic research prototype. The simulator is not
                            the real engine and not for real payment decisions.
                        </span>
                        <span>Python · SQLite · JSONL</span>
                    </div>
                    <Wordmark />
                </div>
            </div>
        </footer>
    );
}
