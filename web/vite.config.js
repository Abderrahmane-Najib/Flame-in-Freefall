import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the API runs on :8000 (python -m uvicorn main:app --reload); Vite forwards these paths to it.
// In production FastAPI serves the built files (web/dist), so the API is on the same address.
const API = "http://localhost:8000";
const API_PATHS = ["/health", "/investigations", "/habitats", "/tests", "/coverage", "/predict", "/graph",
  "/search", "/chat", "/uploads", "/docs", "/openapi.json"];

export default defineConfig({
  plugins: [react()],
  server: { proxy: Object.fromEntries(API_PATHS.map((p) => [p, API])) },
});
