export default function Faq() {
    const questions = [
        {
            question: "Does it move real money?",
            answer: "No. It never authorizes or settles anything, and its scores must not drive real account decisions.",
        },
        {
            question: "Is the fraud real?",
            answer: "No. Labels are scenarios chosen by the generator, so the metrics measure how well a model recovers those patterns.",
        },
        {
            question: "Does the graph actually help?",
            answer: "On the easy profile it did: graph features beat the transaction-only model on PR-AUC, and the paired interval excluded zero. On the hard profile the gain disappeared. See docs/ablation.md.",
        },
        {
            question: "What happens to a duplicate delivery?",
            answer: "SQLite accepts each event ID once, so a retry is ignored and counted as a duplicate.",
        },
        {
            question: "Why is the threshold 0.5?",
            answer: "It is only a demo default. A real threshold would be chosen for a review capacity, measuring the false-positive burden it creates.",
        },
        {
            question: "Do I need to install anything?",
            answer: "Only Python 3.11 or newer. ReportLab is optional and only needed to rebuild the PDF guide.",
        },
    ];

    return (
        <section className="sec wrap" id="faq">
            <div className="center">
                <h2>
                    Any{" "}
                    <i className="tile c-pk">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M9.5 9a2.5 2.5 0 115 0c0 2-2.5 2-2.5 4M12 17.5v.5" />
                        </svg>
                    </i>{" "}
                    <span className="d2">questions?</span>
                </h2>
            </div>
            <div className="faq">
                {questions.map((item) => (
                    <details key={item.question}>
                        <summary>{item.question}</summary>
                        <p>{item.answer}</p>
                    </details>
                ))}
            </div>
        </section>
    );
}
