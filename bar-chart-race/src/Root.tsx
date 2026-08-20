import React from "react";
import { Composition, registerRoot } from "remotion";
import { MainVideo } from "./Composition";

const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AnimatedBarChartRace"
        component={MainVideo}
        durationInFrames={1800}
        fps={60}
        width={1080}
        height={1920}
      />
    </>
  );
};

registerRoot(RemotionRoot);
