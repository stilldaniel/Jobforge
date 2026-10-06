// The browser talks only to this app; /api/* is forwarded to the backend.
// That way any device that can open the app (e.g. a phone over Tailscale)
// can use the API too, and the backend never has to be reachable directly.
const API_URL = process.env.JOBFORGE_API_URL || "http://127.0.0.1:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Lets a second build (e.g. the demo) live beside the laptop's
  // production build in .next without replacing it.
  distDir: process.env.NEXT_DIST_DIR || ".next",

  // FastAPI routes end in "/" (e.g. /jobs/). Keep trailing slashes so
  // proxied requests aren't redirected to the backend's own address.
  skipTrailingSlashRedirect: true,

  async rewrites() {
    return [
      // `:path*` drops a trailing slash, so match those paths first and
      // add it back.
      {
        source: "/api/:path*/",
        destination: `${API_URL}/:path*/`,
      },
      {
        source: "/api/:path*",
        destination: `${API_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
