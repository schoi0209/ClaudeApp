import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { theme } from "../theme";
import {
  TRACKED_COMPANIES,
  COMPANY_COLORS,
  CompanyName,
  formatValue,
  getInterpolatedData,
  getDisplayYear,
} from "../data";

const TOTAL_FRAMES = 960;
const BAR_HEIGHT = 108;
const BAR_GAP = 26;
const ROW_HEIGHT = BAR_HEIGHT + BAR_GAP;
const CHART_TOP = 300;
const LABEL_WIDTH = 270;
const BAR_MAX_WIDTH = 730;


const Scene03_RaceMiddle: React.FC = () => {
  const frame = useCurrentFrame();

  // Entrance animation (first 30 frames)
  const entranceOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Get interpolated data for current frame
  const currentData = getInterpolatedData(frame, TOTAL_FRAMES);

  // Sort to get ranked order
  const ranked = [...currentData].sort((a, b) => b.value - a.value);
  const maxVal = ranked[0]?.value ?? 1;

  // Map company name → rank index (0 = top)
  const rankMap: Record<string, number> = {};
  ranked.forEach((item, idx) => {
    rankMap[item.name] = idx;
  });

  // Display year
  const displayYear = getDisplayYear(frame, TOTAL_FRAMES);

  // Year counter — pulse effect on year change
  const prevYear = getDisplayYear(Math.max(0, frame - 1), TOTAL_FRAMES);
  const yearChanged = displayYear !== prevYear;
  const yearPulse = yearChanged
    ? interpolate(frame % 8, [0, 3, 6], [1.04, 1.06, 1.0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;

  // Grid value markers (0, 500B, 1T, 1.5T, 2T, 2.5T, 3T, 3.5T)
  const gridMarkers = [0, 500, 1000, 1500, 2000, 2500, 3000, 3500];

  // Determine which companies are in top 3 for highlighting
  const top3Names = new Set(ranked.slice(0, 3).map((c) => c.name));

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: theme.colors.bg,
        position: "relative",
        overflow: "hidden",
        opacity: entranceOpacity,
      }}
    >
      {/* Grid lines for value axis */}
      <svg
        width="1080"
        height="1920"
        style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
      >
        {gridMarkers.map((v) => {
          const x = LABEL_WIDTH + (v / 3500) * BAR_MAX_WIDTH;
          if (x > LABEL_WIDTH + BAR_MAX_WIDTH + 2) return null;
          return (
            <g key={v}>
              <line
                x1={x}
                y1={CHART_TOP - 12}
                x2={x}
                y2={CHART_TOP + 10 * ROW_HEIGHT + 12}
                stroke={theme.colors.grid}
                strokeWidth={v === 0 ? 2 : 1}
                strokeDasharray={v === 0 ? undefined : "3 6"}
              />
            </g>
          );
        })}
      </svg>

      {/* Year display — large, dominant */}
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
          transform: `scale(${yearPulse})`,
          transformOrigin: "left center",
          transition: "none",
        }}
      >
        {displayYear}
      </div>

      {/* Grid value axis labels */}
      {gridMarkers.filter((v) => v > 0).map((v) => {
        const x = LABEL_WIDTH + (v / 3500) * BAR_MAX_WIDTH;
        if (x > LABEL_WIDTH + BAR_MAX_WIDTH + 2) return null;
        return (
          <div
            key={v}
            style={{
              position: "absolute",
              top: CHART_TOP - 28,
              left: x - 30,
              width: 60,
              textAlign: "center",
              fontFamily: theme.fonts.body,
              fontSize: 14,
              fontWeight: 400,
              color: theme.colors.fgSubtle,
            }}
          >
            {formatValue(v)}
          </div>
        );
      })}

      {/* Bars — each company always rendered, y position tracks its rank */}
      {TRACKED_COMPANIES.map((name) => {
        const company = currentData.find((d) => d.name === name);
        if (!company) return null;

        const rank = rankMap[name] ?? 9;
        const barWidth = (company.value / maxVal) * BAR_MAX_WIDTH;
        const yPos = CHART_TOP + rank * ROW_HEIGHT;
        const color = COMPANY_COLORS[name as CompanyName];
        const isTop1 = rank === 0;
        const isTop3 = top3Names.has(name);

        return (
          <div
            key={name}
            style={{
              position: "absolute",
              top: yPos,
              left: 0,
              width: 1080,
              height: BAR_HEIGHT,
              // CSS transition drives smooth re-ranking between frames
              transition: "top 0.08s linear",
            }}
          >
            {/* Rank number */}
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

            {/* Company name */}
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
                color: isTop1 ? theme.colors.fg : theme.colors.fg,
              }}
            >
              {name}
            </div>

            {/* Bar fill */}
            <div
              style={{
                position: "absolute",
                top: 10,
                left: LABEL_WIDTH,
                width: Math.max(0, barWidth),
                height: BAR_HEIGHT - 20,
                backgroundColor: color,
                borderRadius: "0 3px 3px 0",
                opacity: isTop1 ? 1 : isTop3 ? 0.92 : 0.78,
              }}
            />

            {/* #1 leader tag */}
            {isTop1 && (
              <div
                style={{
                  position: "absolute",
                  top: 10,
                  left: LABEL_WIDTH + barWidth + 10,
                  height: BAR_HEIGHT - 20,
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                }}
              >
                <span
                  style={{
                    fontFamily: theme.fonts.body,
                    fontSize: 20,
                    fontWeight: 700,
                    color: theme.colors.fg,
                    whiteSpace: "nowrap",
                  }}
                >
                  {formatValue(company.value)}
                </span>
                <span
                  style={{
                    fontFamily: theme.fonts.body,
                    fontSize: 12,
                    fontWeight: 700,
                    color: theme.colors.accent,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    border: `1.5px solid ${theme.colors.accent}`,
                    padding: "3px 8px",
                    borderRadius: 2,
                  }}
                >
                  #1
                </span>
              </div>
            )}

            {/* Value label for non-#1 */}
            {!isTop1 && (
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: LABEL_WIDTH + barWidth + 10,
                  height: BAR_HEIGHT,
                  display: "flex",
                  alignItems: "center",
                  fontFamily: theme.fonts.body,
                  fontSize: 17,
                  fontWeight: 400,
                  color: theme.colors.fgMuted,
                  whiteSpace: "nowrap",
                }}
              >
                {formatValue(company.value)}
              </div>
            )}
          </div>
        );
      })}

      {/* Bottom source */}
      <div
        style={{
          position: "absolute",
          bottom: 64,
          left: 80,
          right: 80,
          display: "flex",
          justifyContent: "space-between",
          fontFamily: theme.fonts.body,
          fontSize: 15,
          fontWeight: 300,
          color: theme.colors.fgMuted,
          opacity: 0.65,
        }}
      >
        <span>Market Capitalization (USD Billions)</span>
        <span>Bloomberg / CompanyMarketCap.com</span>
      </div>
    </div>
  );
};

export default Scene03_RaceMiddle;
