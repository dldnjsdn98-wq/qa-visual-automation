import { defineConfig } from "vitest/config";
export default defineConfig({ test: { environment: "jsdom", include: process.env.QA_API_BASE_URL ? ["tests/integration/*.test.ts"] : ["tests/*.test.{ts,tsx}"], setupFiles: ["./tests/setup.ts"], restoreMocks: true } });
