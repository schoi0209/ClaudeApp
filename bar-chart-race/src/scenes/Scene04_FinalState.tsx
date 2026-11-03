import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { YEARLY_DATA, COMPANY_COLORS, CompanyName, formatValue } from "../data";
import { useEntrance } from "../hooks/useEntrance";

const BAR_HEIGHT = 108;
const BAR_GAP = 26;
const ROW_HEIGHT = BAR_HEIGHT + BAR_GAP;
const CHART_TOP = 290;
const LABEL_WIDTH = 270;
const BAR_MAX_WIDTH = 730;

// Highlight annotation for top company
const NvidiaInsight: React.FC<{ opacity: number }> = ({ opacity }) => (
  <div
    style={{
      position: "absolute",
      top: CHART_TOP + 10,
      left: LABEL_WIDTH + 20,
      opacity,
    }}
  >
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 12,
        backgroundColor: theme.colors.accent,
        color: theme.colors.white,
        fontFamily: theme.fonts.body,
        fontSize: 16,
        fontWeight: 700,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        padding: "8px 16px",
        borderRadius: 3,
      }}
    >
      <span>+18,511% since 2015</span>
    </div>
  </div>
);

const Scene04_FinalState: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const final2024 = YEARLY_DATA[9];
  const sorted = [...final2024.data].sort((a, b) => b.value - a.value);
  const maxVal = sorted[0].value;

  // Entrance
  const entranceOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Exit fade
  const exitOpacity = interpolate(frame, [268, 296], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Header
  const headerProgress = useEntrance(0);
  const headerY = interpolate(headerProgress, [0, 1], [50, 0]);

  // Insight text
  const insightOpacity = interpolate(frame, [50, 75], [0, 1], {
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
        opacity: entranceOpacity * exitOpacity,
      }}
    >
      {/* Subtle grid lines */}
      <svg
        width="1080"
        height="1920"
        style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
      >
        {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => {
          const x = LABEL_WIDTH + (BAR_MAX_WIDTH / 7) * i;
          return (
            <line
              key={i}
              x1={x}
              y1={CHART_TOP - 10}
              x2={x}
              y2={CHART_TOP + sorted.length * ROW_HEIGHT}
              stroke={theme.colors.grid}
              strokeWidth="1"
              strokeDasharray={i === 0 ? undefined : "3 6"}
            />
          );
        })}
      </svg>

      {/* Year display */}
      <div
        style={{
          position: "absolute",
          top: 52,
          left: 80,
          fontFamily: theme.fonts.display,
          fontStyle: "italic",
          fontSize: 152,
          fontWeight: 900,
          color: theme.colors.fg,
          lineHeight: 1,
          letterSpacing: "-4px",
          fontVariationSettings: "'opsz' 144",
          transform: `translateY(${headerY}px)`,
        }}
      >
        2024
      </div>

      {/* "Final Rankings" tag */}
      <div
        style={{
          position: "absolute",
          top: 218,
          left: 84,
          fontFamily: theme.fonts.body,
          fontSize: 16,
          fontWeight: 700,
          color: theme.colors.accent,
          letterSpacing: "0.18em",
          textTransform: "uppercase",
          opacity: interpolate(frame, [20, 40], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        Final Rankings
      </div>

      {/* Bars */}
      {sorted.map((company, rank) => {
        const targetWidth = (company.value / maxVal) * BAR_MAX_WIDTH;
        const barDelay = 5 + rank * 6;
        const barProgress = spring({
          frame: Math.max(0, frame - barDelay),
          fps,
          config: { damping: 14, stiffness: 90, mass: 0.9 },
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
        const isTop1 = rank === 0;
        const isTop3 = rank < 3;

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
            {/* Rank */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 22,
                width: 34,
                height: BAR_HEIGHT,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: theme.fonts.body,
                fontSize: 15,
                fontWeight: 700,
                color: isTop1 ? theme.colors.accent : theme.colors.fgSubtle,
              }}
            >
              {rank + 1}
            </div>

            {/* Name */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 58,
                width: LABEL_WIDTH - 58,
                height: BAR_HEIGHT,
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                paddingRight: 14,
                fontFamily: theme.fonts.body,
                fontSize: isTop1 ? 22 : 19,
                fontWeight: isTop1 ? 700 : isTop3 ? 600 : 500,
                color: theme.colors.fg,
              }}
            >
              {company.name}
            </div>

            {/* Bar */}
            <div
              style={{
                position: "absolute",
                top: 10,
                left: LABEL_WIDTH,
                width: Math.max(0, barWidth),
                height: BAR_HEIGHT - 20,
                backgroundColor: color,
                borderRadius: "0 3px 3px 0",
                opacity: isTop1 ? 1 : isTop3 ? 0.9 : 0.76,
              }}
            />

            {/* Value */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: LABEL_WIDTH + barWidth + 12,
                height: BAR_HEIGHT,
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontFamily: theme.fonts.body,
                fontSize: isTop1 ? 20 : 17,
                fontWeight: isTop1 ? 700 : 400,
                color: isTop1 ? theme.colors.fg : theme.colors.fgMuted,
                whiteSpace: "nowrap",
              }}
            >
              {formatValue(company.value)}
            </div>
          </div>
        );
      })}

      {/* Insight annotation — appears after bars animate in */}
      <NvidiaInsight opacity={insightOpacity * exitOpacity} />

      {/* Insight text block */}
      <div
        style={{
          position: "absolute",
          bottom: 180,
          left: 80,
          right: 80,
          opacity: insightOpacity * exitOpacity,
        }}
      >
        <div
          style={{
            borderLeft: `3px solid ${theme.colors.accent}`,
            paddingLeft: 24,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 24,
              fontWeight: 700,
              color: theme.colors.fg,
              margin: 0,
              lineHeight: 1.3,
            }}
          >
            NVIDIA overtook Apple & Microsoft
            <br />
            to become the world&rsquo;s most valuable company.
          </p>
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 18,
              fontWeight: 400,
              color: theme.colors.fgMuted,
              margin: "10px 0 0",
            }}
          >
            Driven by AI chip demand — $18B → $3.35T in 10 years.
          </p>
        </div>
      </div>

      {/* Source */}
      <div
        style={{
          position: "absolute",
          bottom: 72,
          left: 80,
          right: 80,
          fontFamily: theme.fonts.body,
          fontSize: 15,
          fontWeight: 300,
          color: theme.colors.fgMuted,
          opacity: 0.6,
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        <span>Market Capitalization (USD Billions)</span>
        <span>Bloomberg / CompanyMarketCap.com</span>
      </div>
    </div>
  );
};

export default Scene04_FinalState;
