/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  webpack: (config, { dev, isServer }) => {
    // Triệt tiêu lỗi Cannot find module './[chunk].js' trên Windows:
    // Tắt persistent disk cache trong chế độ dev để tránh desync giữa memory và disk
    if (dev) {
      config.cache = false;
    }
    return config;
  },
  // Tăng thời gian lưu giữ buffer trang trong môi trường dev
  onDemandEntries: {
    maxInactiveAge: 60 * 1000,
    pagesBufferLength: 5,
  },
};

module.exports = nextConfig;
