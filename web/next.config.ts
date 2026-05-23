import type { NextConfig } from "next";

const config: NextConfig = {
  // Les images du Met sont servies sur leur CDN.
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.metmuseum.org" },
    ],
  },
};

export default config;
