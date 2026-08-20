import { frauncesFont, dmSansFont } from "./fonts";

export const theme = {
  colors: {
    bg: "hsl(0, 0%, 96%)",
    bgDark: "hsl(0, 0%, 5%)",
    fg: "hsl(0, 0%, 7%)",
    fgMuted: "hsl(0, 0%, 42%)",
    fgSubtle: "hsl(0, 0%, 62%)",
    fgLight: "hsl(0, 0%, 93%)",
    accent: "hsl(3, 79%, 54%)",
    accentDim: "hsl(3, 60%, 72%)",
    grid: "hsl(0, 0%, 85%)",
    gridDark: "hsl(0, 0%, 18%)",
    white: "hsl(0, 0%, 100%)",
    black: "hsl(0, 0%, 0%)",
  },
  fonts: {
    display: `"${frauncesFont}", Georgia, serif`,
    body: `"${dmSansFont}", "Helvetica Neue", Helvetica, Arial, sans-serif`,
  },
  spacing: {
    xs: 8,
    sm: 16,
    md: 32,
    lg: 64,
    xl: 120,
  },
} as const;

export type Theme = typeof theme;

// Shared spring config per brief
export const SPRING_CONFIG = {
  damping: 12,
  stiffness: 100,
  mass: 0.8,
} as const;
