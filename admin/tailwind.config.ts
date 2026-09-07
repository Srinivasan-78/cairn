/** @type {import('tailwindcss').Config} */

export default {
  content: ["./inertia/**/*.{js,jsx,ts,tsx,edge}", "./resources/**/*.edge"],
  theme: {
    extend: {
      colors: {
        desert: "#EADAB9",
        "desert-green-light": "#BABAAA",
      },
    },
  },
};
