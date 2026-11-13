/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fintech: {
          bg: '#0A0F1D',         // Deep obsidian background
          surface: '#111827',    // Slightly elevated surface
          card: '#1E293B',       // Card background
          border: '#334155',     // Accessible border
          primary: '#3B82F6',    // Brand accent blue
          primaryHover: '#2563EB',
          textMuted: '#94A3B8',  // Secondary text
          textBright: '#F8FAFC', // Main heading text
          profit: '#10B981',     // Green
          loss: '#EF4444',       // Red
          warning: '#F59E0B',    // Amber
        }
      }
    },
  },
  plugins: [],
}
