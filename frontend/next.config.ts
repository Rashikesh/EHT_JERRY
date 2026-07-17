import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false,
  turbopack: {
    root: __dirname,
  },
  allowedDevOrigins :['10.101.199.109'],
};

export default nextConfig;