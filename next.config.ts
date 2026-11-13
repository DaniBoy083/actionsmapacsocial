import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  distDir: process.env.ACTIONS_LOCAL_DEMO === "1" ? ".next-demo" : ".next",
  devIndicators: process.env.ACTIONS_LOCAL_DEMO === "1" ? false : undefined,
  /* config options here */
  experimental: {
    agentFeedback: true,
    // Sessão institucional é validada por requisição; navegação instantânea é opt-in.
    instantInsights: { validationLevel: "manual-warning" },
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
