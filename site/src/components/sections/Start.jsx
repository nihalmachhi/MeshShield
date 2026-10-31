import { useState } from "react";
import { scrollToId } from "../../lib/dom.js";

const STEPS = [
    {
        id: "c1",
        number: "1",
        title: "Create an environment",
        text: "py -3 -m venv .venv; .\\.venv\\Scripts\\Activate.ps1",
        note: "On macOS or Linux: python3 -m venv .venv, then source .venv/bin/activate.",
    },
    {
        id: "c2",
        number: "2",
        title: "Generate, train and evaluate",
        text: ".\scripts\run.ps1 demo",
        note: "On macOS or Linux: PYTHONPATH=src python -m meshshield.cli demo. You can also run generate, train and evaluate on their own.",
    },
    {
        id: "c3",
        number: "3",
        title: "Open the dashboard",
        text: ".\scripts\run.ps1 serve",
        note: "Then visit http://127.0.0.1:8000. It has no authentication, so keep it local.",
    },
];

function CodeRow({ step }) {
    const [label, setLabel] = useState("Copy");
    const copy = () => {
        setLabel("Copied");
        window.setTimeout(() => setLabel("Copy"), 1600);
    };
    return (
        <li>
            <h3>
                <b>{step.number}</b> {step.title}
            </h3>
            <div className="code">
                <code>{step.text}</code>
                <button type="button" onClick={copy}>
                    {label}
                </button>
            </div>
            <p>{step.note}</p>
        </li>
    );
}

export default function Start() {
    return (
        <section className="sec wrap" id="start">
            <div className="center">
                <h2>
                    Running in{" "}
                    <span className="d2">
                        <i className="tile c-k">
                            <svg viewBox="0 0 24 24" aria-hidden="true">
                                <path d="M5 8l4 4-4 4M12 17h7" />
                            </svg>
                        </i>{" "}
                        command.
                    </span>
                </h2>
                <p className="lede">
                    Needs Python 3.11 or newer. No packages to install.
                </p>
            </div>
            <div className="stage" style={{ marginTop: 40 }}>
                <div className="ui" style={{ padding: 12 }}>
                    <ol className="steps">
                        {STEPS.map((step) => (
                            <CodeRow key={step.id} step={step} />
                        ))}
                    </ol>
                </div>
            </div>
            <p className="center" style={{ marginTop: 22 }}>
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
