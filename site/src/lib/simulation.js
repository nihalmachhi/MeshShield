/**
 * Pure-ish simulator engine for the landing page.
 *
 * It follows the Python pipeline's ideas (integrity first, earlier history only,
 * a logistic-style score) but it is illustrative: the weights are hand-set and
 * the data never leaves the browser. The engine is deterministic from its seed
 * and exposes snapshots so React can render without mutating on render.
 */

const SCENARIOS = [
  "normal",
  "high amount",
  "shared device",
  "replay",
  "bad signature",
];
const REVIEW_DEFAULT = 0.5;

function pad(value, width) {
  return String(value).padStart(width, "0");
}

function clock(minutes) {
  const wrapped = ((Math.floor(minutes) % 1440) + 1440) % 1440;
  return `${pad(Math.floor(wrapped / 60), 2)}:${pad(wrapped % 60, 2)}`;
}

export class Simulation {
  constructor(seed = 2025, threshold = REVIEW_DEFAULT) {
    this.initialSeed = seed;
    this.threshold = threshold;
    this.seed = seed;
    this.reset();
  }

  reset() {
    this.seed = this.initialSeed;
    this.now = 540;
    this.count = 0;
    this.delivered = 0;
    this.accepted = 0;
    this.duplicates = 0;
    this.rejected = 0;
    this.seenIds = new Set();
    this.acceptedEvents = [];
    this.history = [];
    this.log = [];
    this.pinned = null;
    for (let index = 0; index < 8; index += 1) this.step("mixed");
  }

  random() {
    this.seed = (Math.imul(this.seed, 1664525) + 1013904223) >>> 0;
    return this.seed / 4294967296;
  }

  gaussian() {
    return (
      (this.random() + this.random() + this.random() + this.random() - 2) * 1.7
    );
  }

  features(event) {
    let accountVelocity = 0;
    let merchantVelocity = 0;
    let past = 0;
    const accounts = new Set([event.account]);
    for (const earlier of this.history) {
      if (earlier.time >= event.time) continue;
      if (earlier.account === event.account) {
        past += 1;
        if (earlier.time >= event.time - 60) accountVelocity += 1;
      }
      if (
        earlier.merchant === event.merchant &&
        earlier.time >= event.time - 60
      ) {
        merchantVelocity += 1;
      }
      if (earlier.device === event.device) accounts.add(earlier.account);
    }
    const devicesAccounts = accounts.size;
    const delay = this.now - event.time;
    return [
      {
        name: "Log amount",
        value: `$${event.amount.toFixed(2)}`,
        contribution: 0.9 * (Math.log(1 + event.amount) - 3.3),
      },
      {
        name: "Delayed sync",
        value: `${delay} min${delay >= 30 ? " (late)" : ""}`,
        contribution: delay >= 30 ? 0.9 : 0,
      },
      {
        name: "Account velocity",
        value: `${accountVelocity} in the last hour`,
        contribution: 0.3 * Math.min(accountVelocity, 5),
      },
      {
        name: "Merchant velocity",
        value: `${merchantVelocity} in the last hour`,
        contribution: 0.1 * (Math.min(merchantVelocity, 8) - 3),
      },
      {
        name: "First payment seen",
        value: past === 0 ? "yes" : `no, ${past} earlier`,
        contribution: past === 0 ? 0.4 : 0,
      },
      {
        name: "Accounts on device",
        value: `${devicesAccounts} ${devicesAccounts === 1 ? "account" : "accounts"}`,
        contribution: 1.2 * Math.min(devicesAccounts - 1, 4),
      },
    ];
  }

  deliver(event) {
    this.delivered += 1;
    const features = this.features(event);
    const rawScore = features.reduce(
      (total, item) => total + item.contribution,
      -2.5,
    );
    const probability = 1 / (1 + Math.exp(-rawScore));
    const findings = [];
    let outcome;
    if (!event.signatureValid) {
      outcome = "rejected";
      this.rejected += 1;
      findings.push("Invalid signature");
    } else if (this.seenIds.has(event.id)) {
      outcome = "duplicate";
      this.duplicates += 1;
      findings.push(`Event ID ${event.id} was already accepted`);
    } else {
      outcome = "accepted";
      this.accepted += 1;
      this.seenIds.add(event.id);
      this.acceptedEvents.push(event);
      this.history.push({
        account: event.account,
        device: event.device,
        merchant: event.merchant,
        time: event.time,
      });
      if (this.history.length > 600) this.history.shift();
    }
    const record = {
      sequence: this.delivered,
      event,
      arrival: this.now,
      features,
      probability,
      outcome,
      findings,
      risky: event.scenario !== "normal",
    };
    this.log.push(record);
    return record;
  }

  step(scenario = "mixed", options = {}) {
    let chosen = scenario;
    if (chosen === "mixed") {
      const draw = this.random();
      chosen =
        draw < 0.78
          ? "normal"
          : draw < 0.84
            ? "high amount"
            : draw < 0.91
              ? "shared device"
              : draw < 0.96
                ? "replay"
                : "bad signature";
    }
    if (chosen === "replay" && this.acceptedEvents.length === 0)
      chosen = "normal";
    this.now += 2;

    let event;
    if (chosen === "replay") {
      const original =
        this.acceptedEvents[
          Math.floor(this.random() * this.acceptedEvents.length)
        ];
      event = {
        id: original.id,
        transaction: original.transaction,
        account: original.account,
        device: original.device,
        merchant: original.merchant,
        amount: original.amount,
        time: original.time,
        signatureValid: true,
        scenario: "replay",
      };
    } else {
      this.count += 1;
      const late = this.random() < 0.2;
      const delay = late
        ? 25 + Math.floor(this.random() * 70)
        : Math.floor(this.random() * 6);
      const account =
        options.account !== undefined
          ? options.account
          : Math.floor(this.random() * 24);
      let device;
      let amount;
      if (chosen === "shared device") {
        device = options.device || `hub_${Math.floor(this.random() * 2)}`;
        amount = Math.exp(4.2 + 0.5 * this.gaussian());
      } else {
        device = `dev_${pad(account, 2)}`;
        amount =
          chosen === "high amount"
            ? 250 + this.random() * 600
            : chosen === "bad signature"
              ? Math.exp(3.8 + 0.6 * this.gaussian())
              : Math.exp(3.2 + 0.5 * this.gaussian());
      }
      event = {
        id: `evt_${pad(this.count, 4)}`,
        transaction: `txn_${pad(this.count, 4)}`,
        account: `acct_${pad(account, 2)}`,
        device,
        merchant: `mer_${Math.floor(this.random() * 8)}`,
        amount: Math.min(amount, 900),
        time: this.now - delay,
        signatureValid: chosen !== "bad signature",
        scenario: chosen,
      };
    }
    return this.deliver(event);
  }

  isReview(record) {
    return record.findings.length > 0 || record.probability >= this.threshold;
  }

  topContribution(record) {
    let best = null;
    for (const feature of record.features) {
      if (
        feature.contribution > 0 &&
        (!best || feature.contribution > best.contribution)
      ) {
        best = feature;
      }
    }
    return best;
  }

  reason(record) {
    if (record.findings.length) return record.findings[0];
    if (record.probability >= this.threshold) {
      const top = this.topContribution(record);
      return `${top ? top.name : "Score"} raised the score`;
    }
    return "No finding, score below the threshold";
  }

  setThreshold(value) {
    this.threshold = value;
  }

  pin(record) {
    this.pinned = record;
  }

  follow() {
    this.pinned = null;
  }

  snapshot() {
    let flagged = 0;
    let truePositives = 0;
    let risky = 0;
    for (const record of this.log) {
      if (record.risky) risky += 1;
      if (this.isReview(record)) {
        flagged += 1;
        if (record.risky) truePositives += 1;
      }
    }
    const devices = new Map();
    for (const row of this.history) {
      if (!devices.has(row.device)) devices.set(row.device, new Set());
      devices.get(row.device).add(row.account);
    }
    const deviceRows = [...devices.entries()]
      .map(([device, accounts]) => ({ device, accounts: accounts.size }))
      .sort(
        (left, right) =>
          right.accounts - left.accounts ||
          left.device.localeCompare(right.device),
      )
      .slice(0, 4);
    const sharedDevices = [...devices.values()].filter(
      (accounts) => accounts.size > 1,
    ).length;
    const selected = this.pinned || this.log[this.log.length - 1] || null;
    return {
      threshold: this.threshold,
      log: this.log,
      delivered: this.delivered,
      accepted: this.accepted,
      duplicates: this.duplicates,
      rejected: this.rejected,
      reviewPercent: this.delivered
        ? Math.round((flagged / this.delivered) * 100)
        : 0,
      flaggedPercent: this.delivered
        ? Math.round((flagged / this.delivered) * 100)
        : 0,
      precision: flagged ? truePositives / flagged : null,
      recall: risky ? truePositives / risky : null,
      risky,
      deviceRows,
      sharedDevices,
      feed: this.log.slice(-8).reverse(),
      selected,
      selectedReason: selected ? this.reason(selected) : "",
      selectedReview: selected ? this.isReview(selected) : false,
      pinned: this.pinned !== null,
    };
  }
}

export { SCENARIOS, REVIEW_DEFAULT, clock, pad };
