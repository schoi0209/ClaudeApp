import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { theme } from "../theme";
import { useEntrance } from "../hooks/useEntrance";

// Subtle grid lines decoration
const GridLines: React.FC<{ opacity: number }> = ({ opacity }) => (
  <svg
    width="1080"
    height="1920"
    style={{ position: "absolute", inset: 0, pointerEvents: "none", opacity }}
    xmlns="http://www.w3.org/2000/svg"
  >
    {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
      <line
        key={i}
        x1={135 * i}
        y1="0"
        x2={135 * i}
        y2="1920"
        stroke={theme.colors.gridDark}
        strokeWidth="1"
      />
    ))}
    {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13].map((i) => (
      <line
        key={i}
        x1="0"
        y1={140 * i}
        x2="1080"
        y2={140 * i}
        stroke={theme.colors.gridDark}
        strokeWidth="1"
      />
    ))}
  </svg>
);

const Scene01_IntroTitle: React.FC = () => {
  const frame = useCurrentFrame();

  // Title entrance
  const titleProgress = useEntrance(0);
  const titleY = interpolate(titleProgress, [0, 1], [80, 0]);
  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Accent bar
  const accentProgress = useEntrance(5);
  const accentScaleX = interpolate(accentProgress, [0, 1], [0, 1]);

  // Subtitle
  const subtitleProgress = useEntrance(12);
  const subtitleY = interpolate(subtitleProgress, [0, 1], [40, 0]);
  const subtitleOpacity = interpolate(frame, [12, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Year range
  const yearProgress = useEntrance(22);
  const yearY = interpolate(yearProgress, [0, 1], [30, 0]);
  const yearOpacity = interpolate(frame, [22, 40], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Source label
  const sourceOpacity = interpolate(frame, [35, 55], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Exit fade
  const exitOpacity = interpolate(frame, [155, 176], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const gridOpacity = interpolate(frame, [0, 40], [0, 0.12], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: theme.colors.bgDark,
        position: "relative",
        overflow: "hidden",
        opacity: exitOpacity,
      }}
    >
      <GridLines opacity={gridOpacity} />

      {/* Left vertical red accent line */}
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 0,
          width: 3,
          height: 1920,
          backgroundColor: theme.colors.accent,
          opacity: interpolate(frame, [20, 50], [0, 0.5], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />

      {/* Main content container */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          paddingLeft: 108,
          paddingRight: 80,
        }}
      >
        {/* Horizontal accent rule */}
        <div
          style={{
            width: 72,
            height: 4,
            backgroundColor: theme.colors.accent,
            marginBottom: 28,
            transformOrigin: "left center",
            transform: `scaleX(${accentScaleX})`,
            opacity: titleOpacity,
          }}
        />

        {/* Display title */}
        <h1
          style={{
            fontFamily: theme.fonts.display,
            fontStyle: "italic",
            fontWeight: 900,
            fontSize: 104,
            lineHeight: 1.0,
            letterSpacing: "-3px",
            color: theme.colors.fgLight,
            margin: 0,
            transform: `translateY(${titleY}px)`,
            opacity: titleOpacity,
            fontVariationSettings: "'opsz' 144",
          }}
        >
          Global
          <br />
          Tech
          <br />
          Giants
        </h1>

        {/* Subtitle */}
        <p
          style={{
            fontFamily: theme.fonts.body,
            fontWeight: 500,
            fontSize: 22,
            color: theme.colors.accent,
            margin: "36px 0 0",
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            transform: `translateY(${subtitleY}px)`,
            opacity: subtitleOpacity * exitOpacity,
          }}
        >
          Market Cap Rankings
        </p>

        {/* Year range */}
        <p
          style={{
            fontFamily: theme.fonts.display,
            fontWeight: 300,
            fontSize: 36,
            color: theme.colors.fgLight,
            margin: "10px 0 0",
            letterSpacing: "0.04em",
            transform: `translateY(${yearY}px)`,
            opacity: yearOpacity * exitOpacity * 0.65,
          }}
        >
          2015 – 2024
        </p>
      </div>

      {/* Bottom source line */}
      <div
        style={{
          position: "absolute",
          bottom: 80,
          left: 108,
          right: 80,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          opacity: sourceOpacity * exitOpacity * 0.45,
        }}
      >
        <span
          style={{
            fontFamily: theme.fonts.body,
            fontSize: 17,
            fontWeight: 300,
            color: theme.colors.fgLight,
            letterSpacing: "0.04em",
          }}
        >
          Source: Bloomberg / CompanyMarketCap.com
        </span>
        <span
          style={{
            fontFamily: theme.fonts.body,
            fontSize: 17,
            fontWeight: 300,
            color: theme.colors.fgLight,
            letterSpacing: "0.04em",
          }}
        >
          USD Billions
        </span>
      </div>
    </div>
  );
};

export default Scene01_IntroTitle;
