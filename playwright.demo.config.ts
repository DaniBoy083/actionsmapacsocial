import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/demo",
  outputDir: "test-results-demo",
  workers: 1,
  fullyParallel: false,
  timeout: 120_000,
  expect: { timeout: 30_000 },
  reporter: "list",
  use: {
    baseURL: "http://localhost:3320",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: {
    command:
      "backend\\.venv\\Scripts\\python.exe scripts/demo.py --frontend-port 3320 --backend-port 8320",
    url: "http://localhost:3320/login",
    reuseExistingServer: false,
    timeout: 120_000,
    env: { APP_ENV: "development", VERCEL: "", PYTHONUTF8: "1" },
  },
});
