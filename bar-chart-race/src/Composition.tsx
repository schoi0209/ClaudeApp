import React from "react";
import { Sequence } from "remotion";
import Scene01_IntroTitle from "./scenes/Scene01_IntroTitle";
import Scene02_RaceStart from "./scenes/Scene02_RaceStart";
import Scene03_RaceMiddle from "./scenes/Scene03_RaceMiddle";
import Scene04_FinalState from "./scenes/Scene04_FinalState";
import Scene05_Outro from "./scenes/Scene05_Outro";
import { FilmGrain } from "./components/FilmGrain";
import { FlashTransition } from "./components/FlashTransition";

// Scene timing (60fps)
// Scene 1:  0  → 179  (180 frames, 3s)
// Scene 2:  180 → 419  (240 frames, 4s)
// Scene 3:  420 → 1379 (960 frames, 16s)
// Scene 4: 1380 → 1679 (300 frames, 5s)
// Scene 5: 1680 → 1799 (120 frames, 2s)
// Total: 1800 frames, 30s

export const MainVideo: React.FC = () => {
  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Scene 1: Intro Title */}
      <Sequence from={0} durationInFrames={180}>
        <Scene01_IntroTitle />
      </Sequence>

      {/* Flash transition: Scene 1 → 2 (centered on frame 179) */}
      <Sequence from={178} durationInFrames={3}>
        <FlashTransition />
      </Sequence>

      {/* Scene 2: Race Start */}
      <Sequence from={180} durationInFrames={240}>
        <Scene02_RaceStart />
      </Sequence>

      {/* Flash transition: Scene 2 → 3 (centered on frame 419) */}
      <Sequence from={418} durationInFrames={3}>
        <FlashTransition />
      </Sequence>

      {/* Scene 3: Race Middle */}
      <Sequence from={420} durationInFrames={960}>
        <Scene03_RaceMiddle />
      </Sequence>

      {/* Flash transition: Scene 3 → 4 (centered on frame 1379) */}
      <Sequence from={1378} durationInFrames={3}>
        <FlashTransition />
      </Sequence>

      {/* Scene 4: Final State */}
      <Sequence from={1380} durationInFrames={300}>
        <Scene04_FinalState />
      </Sequence>

      {/* Flash transition: Scene 4 → 5 (centered on frame 1679) */}
      <Sequence from={1678} durationInFrames={3}>
        <FlashTransition />
      </Sequence>

      {/* Scene 5: Outro */}
      <Sequence from={1680} durationInFrames={120}>
        <Scene05_Outro />
      </Sequence>

      {/* Film grain — always on top across all scenes */}
      <FilmGrain />
    </div>
  );
};
