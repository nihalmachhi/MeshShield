import { scrollToId } from "../../lib/dom.js";

export default function FinalCta() {
    return (
        <section className="wrap">
            <div className="final">
                <svg
                    viewBox="0 0 560 190"
                    role="img"
                    aria-label="A device syncs events to MeshShield, which routes them to accepted, review or rejected"
                >
                    <rect
                        className="nd"
                        x="6"
                        y="68"
                        width="92"
                        height="54"
                        rx="14"
                    />
                    <text x="52" y="100" textAnchor="middle">
                        device
                    </text>
                    <rect
                        className="px"
                        x="200"
                        y="55"
                        width="130"
                        height="80"
                        rx="18"
                    />
                    <text x="265" y="100" textAnchor="middle">
                        MeshShield
                    </text>
                    <rect
                        className="nd"
                        x="440"
                        y="8"
                        width="114"
                        height="46"
                        rx="14"
                    />
                    <text x="497" y="36" textAnchor="middle">
                        accepted
                    </text>
                    <rect
                        className="nd"
                        x="440"
                        y="72"
                        width="114"
                        height="46"
                        rx="14"
                    />
                    <text x="497" y="100" textAnchor="middle">
                        review
                    </text>
                    <rect
                        className="nd"
                        x="440"
                        y="136"
                        width="114"
                        height="46"
                        rx="14"
                    />
                    <text x="497" y="164" textAnchor="middle">
                        rejected
                    </text>
                    <path className="ln" d="M98 95H200" />
                    <path className="ln" d="M330 80C390 80 390 31 440 31" />
                    <path className="ln" d="M330 95H440" />
                    <path className="ln" d="M330 110C390 110 390 159 440 159" />
                </svg>
                <h2>
                    Replay a payment.{" "}
                    <span className="d2">
                        Watch it get{" "}
                        <i className="tile c-r">
                            <svg viewBox="0 0 24 24" aria-hidden="true">
                                <path d="M3 12h4l3-7 4 14 3-7h4" />
                            </svg>
                        </i>{" "}
                        caught.
                    </span>
                </h2>
                <div className="cta">
                    <a
                        className="btn btn-dark"
                        href="https://github.com/nihalmachhi/MeshShield"
                    >
                        View on GitHub
                    </a>
                    <button
                        className="btn btn-ghost"
                        type="button"
                        onClick={() => scrollToId("demo")}
                    >
                        Back to the simulator
                    </button>
                </div>
            </div>
        </section>
    );
}
