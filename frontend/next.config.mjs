   /** @type {import('next').NextConfig} */
   const nextConfig = {
    reactStrictMode: true,
    // ...other config
  }

export default {  
  experimental: {
    optimizePackageImports: ["@radix-ui/react-toast"],
  },
  ...nextConfig,
}