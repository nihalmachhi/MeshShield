import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./styles/base.css";
import "./styles/simulator.css";
import "./styles/simulator-panels.css";
import "./styles/sections.css";
import "./styles/responsive.css";

createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
);
