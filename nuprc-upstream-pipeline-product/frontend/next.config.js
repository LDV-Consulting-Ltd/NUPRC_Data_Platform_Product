/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const backend = process.env.BACKEND_URL || "http://127.0.0.1:8001";
    return [
      {
        source: "/api/backend/:path*",
        destination: backend + "/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
