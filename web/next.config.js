/**** @type {import('next').NextConfig} ****/
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  devIndicators: false,
  allowedDevOrigins: ['*.trycloudflare.com'],  // public tunnel to the dev server
  agentRules: false,  // Next 16 otherwise writes an AGENTS.md into web/
  env: {
    NEXT_PUBLIC_API_WS: process.env.NEXT_PUBLIC_API_WS || 'ws://localhost:8000',
    NEXT_PUBLIC_API_HTTP: process.env.NEXT_PUBLIC_API_HTTP || 'http://localhost:8000',
  }
}

module.exports = nextConfig
