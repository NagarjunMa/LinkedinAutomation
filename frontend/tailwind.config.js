module.exports = {
    content: [
      "./src/app/**/*.{js,ts,jsx,tsx}",
      // Add this line if your components are now here:
      "./src/app/components/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        colors: {
            'custom-gray': '#9BA8AB',
        },
      },
    },
    plugins: [],
}