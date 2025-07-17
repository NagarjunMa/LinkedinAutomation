   /** @type {import('next').NextConfig} */
   const nextConfig = {
    reactStrictMode: true,
  experimental: {
    optimizePackageImports: ['@radix-ui/react-toast'],
  },
  transpilePackages: ['@radix-ui/react-toast', '@radix-ui/react-dialog'],
}

export default nextConfig