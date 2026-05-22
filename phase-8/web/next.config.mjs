/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  /**
   * Override only when you must run `next build` while `next dev` is running:
   * `NEXT_DIST_DIR=.next-build npm run build` (both processes must not share `.next`).
   */
  distDir: process.env.NEXT_DIST_DIR || ".next",

  /**
   * In development, disable webpack's persistent filesystem cache under `.next`.
   * On Windows this cache often goes stale (missing `./*.js` chunks, ENOENT on
   * `vendor-chunks`), which forces killing dev and deleting `.next`.
   */
  webpack: (config, { dev }) => {
    if (dev) {
      config.cache = false;
      // Some Windows / sync folders miss fs events; polling fixes "refresh doesn't show edits".
      if (process.env.NEXT_DEV_POLL === "1") {
        config.watchOptions = {
          poll: 1000,
          aggregateTimeout: 300,
        };
      }
    }
    return config;
  },
};

export default nextConfig;
