import { defineConfig } from "@playwright/test";

export default defineConfig({
    testDir: "./e2e",
    timeout: 30_000,
    retries: 0,
    use: {
        baseURL: "http://127.0.0.1:4173",
        viewport: { width: 1280, height: 900 },
    },
    projects: [
        {
            name: "desktop",
            use: { viewport: { width: 1280, height: 900 } },
        },
        {
            name: "mobile",
            use: { viewport: { width: 375, height: 812 } },
        },
    ],
});
