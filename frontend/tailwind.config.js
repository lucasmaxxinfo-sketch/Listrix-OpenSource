/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)'
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"Roboto Mono"', 'ui-monospace', 'monospace']
      },
      boxShadow: {
        panel: '0 10px 30px rgba(0,0,0,0.35)',
        panelSoft: '0 8px 26px rgba(0,0,0,0.45)',
        orangeGlow: '0 0 0 1px rgba(255,122,26,0.30), 0 0 14px rgba(255,122,26,0.25), 0 10px 30px rgba(0,0,0,0.40)',
        orangeGlowStrong: '0 0 0 1px rgba(255,122,26,0.45), 0 0 26px rgba(255,122,26,0.35), 0 14px 44px rgba(0,0,0,0.50)',
        cyanGlow: '0 0 0 1px rgba(34,211,238,0.25), 0 0 18px rgba(34,211,238,0.20)',
        magentaGlow: '0 0 0 1px rgba(217,70,239,0.25), 0 0 18px rgba(217,70,239,0.20)'
      },
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))'
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))'
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))'
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))'
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))'
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))'
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))'
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        chart: {
          '1': 'hsl(var(--chart-1))',
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))'
        }
      },
      keyframes: {
        'accordion-down': {
          from: {
            height: '0'
          },
          to: {
            height: 'var(--radix-accordion-content-height)'
          }
        },
        'accordion-up': {
          from: {
            height: 'var(--radix-accordion-content-height)'
          },
          to: {
            height: '0'
          }
        },
        'lx-eq': {
          '0%, 100%': { height: '25%' },
          '50%': { height: '100%' }
        },
        'lx-glow-pulse': {
          '0%, 100%': { opacity: '0.75' },
          '50%': { opacity: '1' }
        }
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'lx-eq': 'lx-eq 1s ease-in-out infinite',
        'lx-glow-pulse': 'lx-glow-pulse 2.4s ease-in-out infinite'
      }
    }
  },
  plugins: [require("tailwindcss-animate")],
};