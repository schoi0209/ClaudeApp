import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { theme } from "../theme";
import { useEntrance } from "../hooks/useEntrance";

const Scene05_Outro: React.FC = () => {
  const frame = useCurrentFrame();

  // Entrance
  const entranceOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Exit fade to black
  const exitOpacity = interpolate(frame, [90, 118], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Content entrances
  const logoProgress = useEntrance(5);
  const logoY = interpolate(logoProgress, [0, 1], [50, 0]);

  const sourceProgress = useEntrance(18);
  const sourceY = interpolate(sourceProgress, [0, 1], [30, 0]);
  const sourceOpacity = interpolate(frame, [18, 38], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const nextProgress = useEntrance(32);
  const nextY = interpolate(nextProgress, [0, 1], [30, 0]);
  const nextOpacity = interpolate(frame, [32, 52], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Accent bar scale
  const accentBarScale = interpolate(logoProgress, [0, 1], [0, 1]);

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: theme.colors.bgDark,
        position: "relative",
        overflow: "hidden",
        opacity: entranceOpacity * exitOpacity,
      }}
    >
      {/* Subtle grid */}
      <svg
        width="1080"
        height="1920"
        style={{ position: "absolute", inset: 0, pointerEvents: "none", opacity: 0.08 }}
      >
        {[1, 2, 3, 4, 5, 6, 7].map((i) => (
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
      </svg>

      {/* Left vertical accent line */}
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 0,
          width: 3,
          height: 1920,
          backgroundColor: theme.colors.accent,
          opacity: 0.45,
        }}
      />

      {/* Main content */}
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
          gap: 0,
        }}
      >
        {/* Accent rule */}
        <div
          style={{
            width: 56,
            height: 3,
            backgroundColor: theme.colors.accent,
            marginBottom: 28,
            transformOrigin: "left center",
            transform: `scaleX(${accentBarScale})`,
          }}
        />

        {/* Thank you / series title */}
        <h2
          style={{
            fontFamily: theme.fonts.display,
            fontStyle: "italic",
            fontWeight: 900,
            fontSize: 80,
            lineHeight: 1.05,
            letterSpacing: "-2px",
            color: theme.colors.fgLight,
            margin: 0,
            transform: `translateY(${logoY}px)`,
            fontVariationSettings: "'opsz' 144",
          }}
        >
          Data
          <br />
          Races
        </h2>

        <p
          style={{
            fontFamily: theme.fonts.body,
            fontSize: 19,
            fontWeight: 400,
            color: theme.colors.accentDim,
            margin: "24px 0 0",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            transform: `translateY(${logoY}px)`,
          }}
        >
          Episode 01 · Tech Giants
        </p>

        {/* Divider */}
        <div
          style={{
            width: "100%",
            height: 1,
            backgroundColor: theme.colors.gridDark,
            margin: "48px 0",
            opacity: sourceOpacity,
          }}
        />

        {/* Source attribution */}
        <div
          style={{
            transform: `translateY(${sourceY}px)`,
            opacity: sourceOpacity,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 16,
              fontWeight: 500,
              color: theme.colors.fgSubtle,
              margin: 0,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
            }}
          >
            Data Sources
          </p>
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 20,
              fontWeight: 300,
              color: theme.colors.fgLight,
              margin: "8px 0 0",
              lineHeight: 1.5,
              opacity: 0.75,
            }}
          >
            Bloomberg Terminal
            <br />
            CompanyMarketCap.com
            <br />
            Yahoo Finance Historical Data
          </p>
        </div>

        {/* Divider */}
        <div
          style={{
            width: "100%",
            height: 1,
            backgroundColor: theme.colors.gridDark,
            margin: "48px 0",
            opacity: nextOpacity,
          }}
        />

        {/* Next episode teaser */}
        <div
          style={{
            transform: `translateY(${nextY}px)`,
            opacity: nextOpacity,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 16,
              fontWeight: 500,
              color: theme.colors.accent,
              margin: 0,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
            }}
          >
            Up Next
          </p>
          <p
            style={{
              fontFamily: theme.fonts.display,
              fontStyle: "italic",
              fontSize: 40,
              fontWeight: 700,
              color: theme.colors.fgLight,
              margin: "10px 0 0",
              lineHeight: 1.2,
              letterSpacing: "-1px",
              fontVariationSettings: "'opsz' 72",
            }}
          >
            Global EV Sales Race
            <br />
            2018 – 2024
          </p>
        </div>
      </div>

      {/* Bottom footnote */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          left: 108,
          right: 80,
          fontFamily: theme.fonts.body,
          fontSize: 14,
          fontWeight: 300,
          color: theme.colors.fgLight,
          opacity: nextOpacity * 0.35,
          letterSpacing: "0.04em",
        }}
      >
        All data approximate · Figures represent year-end market capitalizations
      </div>
    </div>
  );
};

export default Scene05_Outro;
