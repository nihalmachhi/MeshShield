# MeshShield: how it works

## In one sentence

MeshShield creates a small fictional offline-payment network, replays its delayed and duplicated messages, learns patterns from past synthetic activity, and shows the resulting review evidence in a local browser.

## What happens when you run the demo

1. **Generate a fictional world.** A fixed random seed creates accounts, devices, merchants, transaction amounts, event times, and scenario labels. The dataset card records the seed and the actual scenario counts.
2. **Create offline activity.** Some transactions wait before upload. Each record keeps both the time it happened and the time it arrived, which is essential when events synchronize late.
3. **Deliver sync messages imperfectly.** The simulator inserts duplicate deliveries and reorders a few messages. SQLite's unique event ID ensures a retry does not apply the same event twice. Invalid simulated signatures are rejected.
4. **Build historical features.** The pipeline sorts the network by event time. Before adding a transaction to history, it counts earlier account activity, merchant activity, and device/account relationships. This avoids giving an earlier prediction information from its future.
5. **Fit and compare models.** A compact logistic regression learns weights from earlier events. The pipeline trains one version with graph-derived features and one without them, then compares both with simple rules on the later 20% of events.
6. **Inspect results.** The browser dashboard displays model metrics, the synchronization summary, a synthetic review queue, and the largest model contributions for a selected transaction.

## Important vocabulary

- **Transaction event:** the simulated payment action.
- **Sync event:** the message that carries that action from an offline device to the local service.
- **Idempotency:** processing the same sync event repeatedly has the effect of processing it once.
- **Graph feature:** a numerical summary of relationships, such as how many accounts previously used a device.
- **Holdout:** later records that are kept out of model fitting and used for a basic evaluation.
- **Contribution:** a model input's signed effect on the fitted logistic score. It is an association, not proof of cause.

## See the project

Follow the setup in the repository README. `demo` regenerates the data and metrics; `serve` starts the UI at `http://127.0.0.1:8000`. Click **Replay sync event** to send the same event twice. Select a table row to inspect its scenario, integrity findings, model contributions, and review reasoning.

## What this demo does not prove

The data is invented, and the positive labels come from the generator itself. A model that recognizes these labels has not proven it can detect real fraud. The threshold is selected from a separate synthetic calibration interval using example cost and review-capacity values; those inputs are not operational recommendations. Performance, calibration, fairness, and false-positive impact have not been validated for a real payment environment. No real money is moved and no payment is approved or declined.
