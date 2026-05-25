import React from "react";
import { useCurrentFrame } from "remotion";

interface FlashTransitionProps {
  color?: string;
}

/**
 * 3-frame flash: opacity peaks on frame 1 (the centre frame).
 * Wrap in <Sequence from={N-1} durationInFrames={3}> at each scene boundary.
 */
export const FlashTransition: React.FC<FlashTransitionProps> = ({
  color = "hsl(0, 0%, 100%)",
}) => {
  const frame = useCurrentFrame();
  const opacity = frame === 1 ? 0.85 : 0;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: color,
        opacity,
        zIndex: 998,
        pointerEvents: "none",
      }}
    />
  );
};
