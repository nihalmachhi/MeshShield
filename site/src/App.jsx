import { useEffect, useRef, useState } from "react";
import Header from "./components/Header.jsx";
import MarketingSections from "./components/MarketingSections.jsx";
import PaymentDemo from "./components/PaymentDemo.jsx";

const MODES = [
    "mixed",
    "ordinary",
    "high amount",
    "shared device",
    "replay",
    "bad signature",
];

export default function App() {
    const [mode, setMode] = useState("mixed");
    const [payments, setPayments] = useState([]);
    const [paused, setPaused] = useState(false);
    const [dark, setDark] = useState(true);
    const [selected, setSelected] = useState(null);
    const sequence = useRef(0);

    useEffect(() => {
        document.documentElement.dataset.theme = dark ? "dark" : "light";
    }, [dark]);

    function sendPayment(selectedMode = mode) {
        const nextNumber = sequence.current + 1;
        sequence.current = nextNumber;
        const scenario =
            selectedMode === "mixed"
                ? [
                      "ordinary",
                      "ordinary",
                      "ordinary",
                      "high amount",
                      "shared device",
                      "replay",
                      "bad signature",
                  ][Math.floor(Math.random() * 7)]
                : selectedMode;
        const accountIndex = Math.floor(Math.random() * 24);
        const account = `acct_${String(accountIndex).padStart(2, "0")}`;
        const device =
            scenario === "shared device"
                ? "shared_01"
                : `dev_${String(accountIndex % 12).padStart(2, "0")}`;
        const amount =
            scenario === "high amount"
                ? 250 + Math.random() * 600
                : 12 + Math.random() * 180;
        const signatureValid = scenario !== "bad signature";
        const eventId = `evt_${String(scenario === "replay" && nextNumber > 1 ? nextNumber - 1 : nextNumber).padStart(5, "0")}`;
        const duplicate = scenario === "replay" && nextNumber > 1;
        const factors = [
            ["amount pattern", (Math.log(1 + amount) - 3.6) * 1.5],
            ["device reuse", scenario === "shared device" ? 0.9 : -0.3],
            ["delayed sync", Math.random() > 0.78 ? 1.1 : -0.3],
        ].sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
        const rawScore =
            -2.3 + factors.reduce((total, [, value]) => total + value, 0);
        const risk = 1 / (1 + Math.exp(-rawScore));
        const payment = {
            id: `txn_${String(nextNumber).padStart(5, "0")}`,
            eventId,
            account,
            device,
            amount,
            risk,
            scenario,
            factors,
            signatureValid,
            duplicate,
            time: new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
            }),
            review: !signatureValid || duplicate || risk >= 0.5,
        };
        setPayments((current) => [payment, ...current].slice(0, 18));
        setSelected(payment);
    }

    function runBatch() {
        for (let index = 0; index < 8; index += 1) sendPayment();
    }

    useEffect(() => {
        if (paused) return undefined;
        const timer = window.setInterval(() => sendPayment(), 1800);
        return () => window.clearInterval(timer);
    }, [paused, mode]);

    const accepted = payments.filter(
        (payment) => payment.signatureValid && !payment.duplicate,
    ).length;
    const duplicates = payments.filter((payment) => payment.duplicate).length;
    const rejected = payments.filter(
        (payment) => !payment.signatureValid,
    ).length;
    const reviewCount = payments.filter((payment) => payment.review).length;

    return (
        <>
            <Header
                dark={dark}
                paused={paused}
                onPauseToggle={() => setPaused((value) => !value)}
                onThemeToggle={() => setDark((value) => !value)}
            />
            <main id="main" className="wrap">
                <PaymentDemo
                    mode={mode}
                    setMode={setMode}
                    modes={MODES}
                    payments={payments}
                    sendPayment={sendPayment}
                    runBatch={runBatch}
                    onReset={() => {
                        setPayments([]);
                        setSelected(null);
                        sequence.current = 0;
                    }}
                    accepted={accepted}
                    duplicates={duplicates}
                    rejected={rejected}
                    reviewCount={reviewCount}
                    selected={selected}
                    setSelected={setSelected}
                />
                <MarketingSections />
            </main>
        </>
    );
}
