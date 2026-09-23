import React from "react";
import { useCurrentFrame } from "remotion";

/**
 * Animated film grain using SVG feTurbulence with a per-frame seed.
 * Rendered with mix-blend-mode:overlay for subtle texture.
 */
export const FilmGrain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 1000,
        pointerEvents: "none",
        mixBlendMode: "overlay",
        opacity: 0.06,
      }}
    >
      <svg
        width="1080"
        height="1920"
        xmlns="http://www.w3.org/2000/svg"
        style={{ display: "block" }}
      >
        <filter id={`grain-${frame}`}>
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.72"
            numOctaves="4"
            seed={frame}
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect
          width="1080"
          height="1920"
          filter={`url(#grain-${frame})`}
          opacity="1"
        />
      </svg>
    </div>
  );
};
