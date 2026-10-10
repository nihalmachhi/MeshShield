"""Build the readable, measured MeshShield project walkthrough PDF."""

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "MeshShield_How_It_Works.pdf"
METRICS = json.loads((ROOT / "data" / "generated" / "metrics.json").read_text(encoding="utf-8"))
CARD = json.loads((ROOT / "data" / "generated" / "dataset_card.json").read_text(encoding="utf-8"))
INK = colors.HexColor("#14243a")
MUTED = colors.HexColor("#566b81")
TEAL = colors.HexColor("#087f78")
PALE = colors.HexColor("#eaf5f3")
LINE = colors.HexColor("#d8e1e8")
AMBER = colors.HexColor("#fff4dd")


def p(text, style="Body"):
    return Paragraph(text, STYLES[style])


def bullet(text):
    return Paragraph("- " + text, STYLES["Bulletx"])


def callout(title, body, background=PALE):
    cell = [p(f"<b>{title}</b>", "CalloutTitle"), p(body, "Callout")]
    table = Table([[cell]], colWidths=[166 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return table


def make_table(rows, widths, header=True):
    converted = [[p(str(value), "TableHead" if header and ri == 0 else "TableCell")
                  for value in row] for ri, row in enumerate(rows)]
    table = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), INK))
        if len(rows) > 1:
            commands.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fa")]))
    table.setStyle(TableStyle(commands))
    return table


def draw_page(canvas, doc):
    canvas.saveState()
    page_width, page_height = A4
    if doc.page > 1:
        canvas.setStrokeColor(LINE)
        canvas.line(22 * mm, page_height - 16 * mm, page_width - 22 * mm, page_height - 16 * mm)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(TEAL)
        canvas.drawString(22 * mm, page_height - 12.5 * mm, "MESHSHIELD  /  PROJECT WALKTHROUGH")
    canvas.setStrokeColor(LINE)
    canvas.line(22 * mm, 15 * mm, page_width - 22 * mm, 15 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(22 * mm, 10 * mm, "Synthetic research demo - not a production payment system")
    canvas.drawRightString(page_width - 22 * mm, 10 * mm, str(doc.page))
    canvas.restoreState()


STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="CoverEyebrow", parent=STYLES["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=13, textColor=TEAL, alignment=TA_CENTER, spaceAfter=13))
STYLES.add(ParagraphStyle(name="CoverTitle", parent=STYLES["Title"], fontName="Helvetica-Bold", fontSize=34, leading=39, textColor=INK, alignment=TA_CENTER, spaceAfter=12))
STYLES.add(ParagraphStyle(name="CoverSub", parent=STYLES["Normal"], fontName="Helvetica", fontSize=16, leading=22, textColor=MUTED, alignment=TA_CENTER, spaceAfter=22))
STYLES.add(ParagraphStyle(name="H1x", parent=STYLES["Heading1"], fontName="Helvetica-Bold", fontSize=21, leading=26, textColor=INK, spaceBefore=4, spaceAfter=12))
STYLES.add(ParagraphStyle(name="H2x", parent=STYLES["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=TEAL, spaceBefore=9, spaceAfter=5))
STYLES.add(ParagraphStyle(name="Body", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=9, leading=13.5, textColor=INK, spaceAfter=7))
STYLES.add(ParagraphStyle(name="Bulletx", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=8.7, leading=12.5, leftIndent=10, firstLineIndent=-8, textColor=INK, spaceAfter=4))
STYLES.add(ParagraphStyle(name="Small", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED, spaceAfter=4))
STYLES.add(ParagraphStyle(name="CalloutTitle", parent=STYLES["BodyText"], fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=INK, spaceAfter=3))
STYLES.add(ParagraphStyle(name="Callout", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=8.5, leading=12, textColor=INK, spaceAfter=0))
STYLES.add(ParagraphStyle(name="TableHead", parent=STYLES["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white, spaceAfter=0))
STYLES.add(ParagraphStyle(name="TableCell", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=7.6, leading=10.5, textColor=INK, spaceAfter=0))
STYLES.add(ParagraphStyle(name="Center", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=10, leading=15, textColor=MUTED, alignment=TA_CENTER))


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=22 * mm, leftMargin=22 * mm,
                            topMargin=23 * mm, bottomMargin=22 * mm,
                            title="MeshShield - How It Works and How to Run It",
                            author="MeshShield project documentation")
    story = [Spacer(1, 25 * mm), p("A LOCAL AI ENGINEERING PROJECT", "CoverEyebrow"),
             p("MeshShield", "CoverTitle"),
             p("How it works, how to run it, and how to read the results", "CoverSub"),
             Spacer(1, 6 * mm),
             callout("The short version", "MeshShield generates a fictional offline-payment network, simulates delayed and repeated sync messages, builds features from past activity, and compares two small risk models with simple rules."),
             Spacer(1, 9 * mm), p("Project at a glance", "H2x"),
             make_table([["Piece", "What it does"],
                         ["Data", f"{CARD['transaction_count']:,} reproducible, synthetic transactions (seed {CARD['seed']})"],
                         ["Model", "Dependency-free logistic regression with and without graph-derived features"],
                         ["Storage", "Inspect-able JSON Lines datasets and a SQLite idempotency store"],
                         ["Interface", "Local browser dashboard and small JSON API"],
                         ["Runtime", "Python 3.11+; standard library only"],
                         ], [38 * mm, 128 * mm]),
             Spacer(1, 10 * mm), p("A learning and portfolio project. No payment is authorized, settled, or moved.", "Center"),
             PageBreak(), p("01  /  THE SYSTEM", "H1x"),
             p("MeshShield is a research simulator that sits beside a hypothetical payment system. It receives fictional events, checks their integrity, scores risk for review, and preserves evidence about why a record was flagged."),
             p("From offline transaction to review", "H2x"),
             make_table([["Step", "What happens", "Why it matters"],
                         ["1. Create", "Seeded generator creates accounts, devices, merchants, amounts, timestamps, and scenario labels.", "Same seed reproduces the same demo."],
                         ["2. Queue", "A transaction can reach the service after its event time; both event and arrival times are retained.", "Delayed synchronization is visible."],
                         ["3. Deliver", "Sync messages may be duplicated or reordered. SQLite accepts each event ID once.", "Retries do not apply an event twice."],
                         ["4. Build features", "Past account, merchant, and device activity is counted before adding the current event.", "The current event cannot use its own or future history."],
                         ["5. Score", "A logistic model scores the transaction; deterministic integrity findings are shown separately.", "Risk estimates and hard checks are not conflated."],
                         ["6. Review", "Dashboard shows holdout metrics, delivery behavior, transaction evidence, and model contributions.", "A human can inspect the simulated evidence."],
                         ], [23 * mm, 82 * mm, 61 * mm]),
             Spacer(1, 5 * mm),
             callout("System boundary", "The local service is for a single-user demonstration. It has no authentication and binds to 127.0.0.1. It has no connection to payment rails, account providers, or real customer data.", AMBER),
             p("Project structure", "H2x"),
             p("src/meshshield/ separates the event contracts, generator, feature pipeline, rules, model, evaluation, simulator, storage, CLI, and web server. frontend/ contains the dashboard. docs/ explains data, features, evaluation, and safe use."),
             PageBreak(), p("02  /  MODEL AND EVALUATION", "H1x"),
             p("Two logistic-regression models use the same chronological training window. The transaction baseline uses amount, time, velocity, and sync-delay features. The graph model adds historical device/account relationship summaries. A hand-authored rule score gives a simpler third comparison."),
             p("How to read the demo run", "H2x"),
             make_table([["Metric", "Graph model", "Transaction baseline", "Rules only"],
                         ["Precision", f"{METRICS['graph_model']['precision']:.3f}", f"{METRICS['non_graph_model']['precision']:.3f}", f"{METRICS['rule_only_baseline']['precision']:.3f}"],
                         ["Recall", f"{METRICS['graph_model']['recall']:.3f}", f"{METRICS['non_graph_model']['recall']:.3f}", f"{METRICS['rule_only_baseline']['recall']:.3f}"],
                         ["F1", f"{METRICS['graph_model']['f1']:.3f}", f"{METRICS['non_graph_model']['f1']:.3f}", f"{METRICS['rule_only_baseline']['f1']:.3f}"],
                         ["Average precision", f"{METRICS['graph_model']['pr_auc_average_precision']:.3f}", f"{METRICS['non_graph_model']['pr_auc_average_precision']:.3f}", f"{METRICS['rule_only_baseline']['pr_auc_average_precision']:.3f}"],
                         ["Brier score", f"{METRICS['graph_model']['brier_score']:.3f}", f"{METRICS['non_graph_model']['brier_score']:.3f}", f"{METRICS['rule_only_baseline']['brier_score']:.3f}"],
                         ["Review rate @ 0.5", f"{METRICS['graph_model']['review_rate']:.1%}", f"{METRICS['non_graph_model']['review_rate']:.1%}", f"{METRICS['rule_only_baseline']['review_rate']:.1%}"],
                         ], [42 * mm, 39 * mm, 43 * mm, 42 * mm]),
             Spacer(1, 4 * mm),
             p(f"Measured run: {METRICS['dataset']['train']:,} training events and {METRICS['dataset']['test']:,} later holdout events, with {METRICS['graph_model']['positive_count']:,} positive scenario labels in holdout. Seed: {CARD['seed']}.", "Small"),
             callout("Interpretation", "The graph model did not improve average precision over the transaction-only baseline in this run. The rule score had higher precision at the displayed threshold but lower recall. These results show how to compare methods on this generator; they do not demonstrate real-world fraud performance.", AMBER),
             p("The split is chronological: the earliest 80% trains each model and the later 20% is held out. Average precision summarizes precision across ranking thresholds. The 0.5 cut-off is illustrative, not chosen for a real analyst capacity. The Brier score is reported as probability error; calibration has not been established."),
             PageBreak(), p("03  /  RUN IT LOCALLY", "H1x"),
             p("Requires Python 3.11 or newer. The app has no external runtime dependencies. Open PowerShell in the project directory and run:"),
             callout("One-time setup", "py -3 -m venv .venv<br/>.\\.venv\\Scripts\\Activate.ps1"),
             Spacer(1, 3 * mm), callout("Generate data, train, and evaluate", ".\\scripts\\run.ps1 demo"),
             Spacer(1, 3 * mm), callout("Start the dashboard", ".\\scripts\\run.ps1 serve<br/>Then open http://127.0.0.1:8000 in your browser."),
             p("Useful commands", "H2x"),
             make_table([["Command", "Use"],
                         [".\\scripts\\run.ps1 generate --count 1600 --seed 2025", "Recreate the synthetic dataset and dataset card."],
                         [".\\scripts\\run.ps1 train", "Fit both model variants and write holdout metrics."],
                         [".\\scripts\\run.ps1 evaluate", "Print the saved evaluation results."],
                         [".\\scripts\\run.ps1 serve --port 8000", "Run the local UI and API."],
                         ], [88 * mm, 78 * mm]),
             p("Generated artifacts", "H2x"),
             p("data/generated/transactions.jsonl and sync_events.jsonl contain the synthetic records. dataset_card.json records the seed, class counts, and limitations. model.json and baseline_model.json hold model weights; metrics.json holds the evaluation. meshshield.sqlite3 persists accepted event IDs."),
             p("Use the dashboard", "H2x"),
             bullet("Read the comparison at the top. It is calculated from the later time holdout."),
             bullet("Review the delivery summary to see duplicates ignored and invalid signatures rejected."),
             bullet("Filter the table and select a transaction to inspect its scenario, integrity checks, and model contributions."),
             bullet("Click Replay sync event. The API submits an event twice and reports that the retry was ignored."),
             p("Local API: GET /api/health, GET /api/metrics, GET /api/transactions?limit=100, GET /api/transactions/{id}, and POST /api/replay."),
             PageBreak(), p("04  /  LIMITATIONS AND NEXT STEPS", "H1x"),
             callout("Synthetic labels are not confirmed fraud", "The generator writes the positive label because it injected a scenario. A model can learn those artificial patterns very well and still fail on real events. All reported metrics refer only to this synthetic holdout.", AMBER),
             p("Safe interpretation", "H2x"),
             bullet("Treat risk scores as a learning aid, never as a payment approval or decline."),
             bullet("A shared device, high amount, or delayed sync can have legitimate explanations."),
             bullet("Model contributions show associations in a fitted model; they do not establish cause or intent."),
             bullet("The simulated signature check is a Boolean field, not cryptographic verification."),
             bullet("The server has no login. Keep it bound to your own computer; do not expose it to a network."),
             p("Possible research extensions", "H2x"),
             make_table([["Extension", "Question to answer first"],
                         ["Scenario holdout", "Does performance survive when an entire generated scenario is absent from training?"],
                         ["Review capacity", "What precision and recall can be achieved for a fixed analyst review budget?"],
                         ["Calibration", "Do predicted probabilities match outcome frequencies on independent labels?"],
                         ["Robustness", "How does late synchronization, clock skew, or a changing device network affect results?"],
                         ["Authorized data", "Can outcomes and privacy protections be independently validated before any real-data experiment?"],
                         ], [40 * mm, 126 * mm]),
             Spacer(1, 8 * mm),
             callout("More detail", "Start with README.md. The docs/ folder contains the system model, synthetic data card, feature contract, evaluation protocol, threat model, and a text walkthrough."),
             Spacer(1, 6 * mm), p("Built as a clean, local, reproducible portfolio project. Results are reported as measured from the generated run above.", "Center")]
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(OUT)


if __name__ == "__main__":
    build()
