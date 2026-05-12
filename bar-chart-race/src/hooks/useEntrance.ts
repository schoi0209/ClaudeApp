import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SPRING_CONFIG } from "../theme";

/**
 * Returns a spring progress value (0 → ~1) starting from `delay` frames.
 * Uses the project-wide spring config from the brief.
 */
export function useEntrance(delay = 0): number {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({
    frame: Math.max(0, frame - delay),
    fps,
    config: SPRING_CONFIG,
  });
}

/**
 * Returns a spring progress for a custom spring config.
 */
export function useSpring(
  delay = 0,
  config: { damping: number; stiffness: number; mass: number } = SPRING_CONFIG
): number {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({
    frame: Math.max(0, frame - delay),
    fps,
    config,
  });
}
