const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: path.join(__dirname),
  },
  reactCompiler: true,
  async redirects() {
    return [
      { source: "/control-panel", destination: "/console/pipeline", permanent: false },
      { source: "/run-history", destination: "/console/runs", permanent: false },
      { source: "/apis", destination: "/docs", permanent: false },
    ];
  },
  async rewrites() {
    const backend = process.env.BACKEND_URL || "http://127.0.0.1:8000";
    return [
      {
        source: "/api/backend/:path*",
        destination: backend + "/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
