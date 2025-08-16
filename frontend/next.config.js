/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  // Disable font optimization to fix PostCSS error
  optimizeFonts: false,
  // Alternative: disable swc minify if needed
  swcMinify: false,
}

module.exports = nextConfig