import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { YEARLY_DATA, COMPANY_COLORS, CompanyName, formatValue } from "../data";
import { useEntrance } from "../hooks/useEntrance";

const BAR_HEIGHT = 108;
const BAR_GAP = 26;
const ROW_HEIGHT = BAR_HEIGHT + BAR_GAP;
const CHART_TOP = 300;
const LABEL_WIDTH = 270;
const BAR_MAX_WIDTH = 730;

const Scene02_RaceStart: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const year2015 = YEARLY_DATA[0];
  const sorted = [...year2015.data].sort((a, b) => b.value - a.value);
  const maxVal = sorted[0].value;

  // Header entrance
  const headerProgress = useEntrance(0);
  const headerY = interpolate(headerProgress, [0, 1], [60, 0]);
  const headerOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Exit fade
  const exitOpacity = interpolate(frame, [210, 236], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: theme.colors.bg,
        position: "relative",
        overflow: "hidden",
        opacity: exitOpacity,
      }}
    >
      {/* Subtle grid lines */}
      <svg
        width="1080"
        height="1920"
        style={{ position: "absolute", inset: 0, pointerEvents: "none", opacity: 0.5 }}
      >
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <line
            key={i}
            x1={LABEL_WIDTH + (BAR_MAX_WIDTH / 5) * i}
            y1={CHART_TOP}
            x2={LABEL_WIDTH + (BAR_MAX_WIDTH / 5) * i}
            y2={CHART_TOP + sorted.length * ROW_HEIGHT}
            stroke={theme.colors.grid}
            strokeWidth="1"
            strokeDasharray="4 6"
          />
        ))}
      </svg>

      {/* Year display */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 80,
          fontFamily: theme.fonts.display,
          fontStyle: "italic",
          fontSize: 148,
          fontWeight: 900,
          color: theme.colors.fg,
          lineHeight: 1,
          letterSpacing: "-4px",
          transform: `translateY(${headerY}px)`,
          opacity: headerOpacity,
          fontVariationSettings: "'opsz' 144",
        }}
      >
        2015
      </div>

      {/* Title tag */}
      <div
        style={{
          position: "absolute",
          top: 215,
          left: 82,
          fontFamily: theme.fonts.body,
          fontSize: 16,
          fontWeight: 500,
          color: theme.colors.accent,
          letterSpacing: "0.18em",
          textTransform: "uppercase",
          opacity: interpolate(frame, [15, 35], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        Starting Position
      </div>

      {/* Bars */}
      {sorted.map((company, rank) => {
        const targetWidth = (company.value / maxVal) * BAR_MAX_WIDTH;
        const barDelay = 10 + rank * 7;
        const barProgress = spring({
          frame: Math.max(0, frame - barDelay),
          fps,
          config: { damping: 18, stiffness: 110, mass: 0.7 },
        });
        const barWidth = interpolate(barProgress, [0, 1], [0, targetWidth]);
        const itemOpacity = interpolate(
          frame - barDelay,
          [0, 12],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );

        const y = CHART_TOP + rank * ROW_HEIGHT;
        const color = COMPANY_COLORS[company.name as CompanyName];
        const isTop = rank === 0;

        return (
          <div
            key={company.name}
            style={{
              position: "absolute",
              top: y,
              left: 0,
              width: 1080,
              height: BAR_HEIGHT,
              opacity: itemOpacity,
            }}
          >
            {/* Rank number */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 24,
                width: 36,
                height: BAR_HEIGHT,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: theme.fonts.body,
                fontSize: 16,
                fontWeight: 700,
                color: isTop ? theme.colors.accent : theme.colors.fgSubtle,
              }}
            >
              {rank + 1}
            </div>

            {/* Company name */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 64,
                width: LABEL_WIDTH - 64,
                height: BAR_HEIGHT,
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                paddingRight: 14,
                fontFamily: theme.fonts.body,
                fontSize: 20,
                fontWeight: isTop ? 700 : 500,
                color: theme.colors.fg,
              }}
            >
              {company.name}
            </div>

            {/* Bar */}
            <div
              style={{
                position: "absolute",
                top: 8,
                left: LABEL_WIDTH,
                width: barWidth,
                height: BAR_HEIGHT - 16,
                backgroundColor: color,
                borderRadius: "0 3px 3px 0",
              }}
            />

            {/* Value label */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: LABEL_WIDTH + barWidth + 12,
                height: BAR_HEIGHT,
                display: "flex",
                alignItems: "center",
                fontFamily: theme.fonts.body,
                fontSize: 18,
                fontWeight: 400,
                color: theme.colors.fgMuted,
                whiteSpace: "nowrap",
              }}
            >
              {formatValue(company.value)}
            </div>
          </div>
        );
      })}

      {/* Bottom label */}
      <div
        style={{
          position: "absolute",
          bottom: 72,
          left: 80,
          right: 80,
          fontFamily: theme.fonts.body,
          fontSize: 16,
          fontWeight: 300,
          color: theme.colors.fgMuted,
          letterSpacing: "0.04em",
          opacity: interpolate(frame, [50, 70], [0, 0.6], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        Market Capitalization (USD Billions) · Bloomberg / CompanyMarketCap.com
      </div>
    </div>
  );
};

export default Scene02_RaceStart;
