# Animated Bar Chart Race — Global Tech Giants

A production-ready Remotion 4 video: **Top 10 Global Tech Companies by Market Cap (2015–2024)**.

**Resolution**: 1080 × 1920 · **FPS**: 60 · **Duration**: 30s (1800 frames)

---

## Quick Start

```bash
npm install
npx remotion studio
```

Then open `http://localhost:3000` in your browser.

## Render to video

```bash
npx remotion render AnimatedBarChartRace out/video.mp4
```

## Type-check

```bash
npm run typecheck
```

---

## Project Structure

```
src/
  Root.tsx              ← Composition registration + registerRoot
  Composition.tsx       ← MainVideo: all scenes + flash transitions + film grain
  scenes/
    Scene01_IntroTitle.tsx   (frames   0–179,  3s)
    Scene02_RaceStart.tsx    (frames 180–419,  4s)
    Scene03_RaceMiddle.tsx   (frames 420–1379, 16s)
    Scene04_FinalState.tsx   (frames 1380–1679, 5s)
    Scene05_Outro.tsx        (frames 1680–1799, 2s)
  components/
    FilmGrain.tsx       ← SVG feTurbulence grain, mix-blend-mode: overlay
    FlashTransition.tsx ← 1-frame white flash between scenes
  hooks/
    useEntrance.ts      ← spring() helper with project-wide config
  theme.ts              ← Colors (HSL), typography, spacing tokens
  fonts.ts              ← @remotion/google-fonts loader: Fraunces + DM Sans
  data.ts               ← Market cap dataset, interpolation utilities
public/
  voiceover.mp3         ← (generate from voiceover.txt — see below)
voiceover.txt           ← Script + production notes
```

---

## Design System

| Token | Value |
|-------|-------|
| `bg` | `hsl(0, 0%, 96%)` — light scenes |
| `bgDark` | `hsl(0, 0%, 5%)` — dark scenes |
| `accent` | `hsl(3, 79%, 54%)` — Swiss red |
| Display font | Fraunces (italic, opsz 144) via `@remotion/google-fonts` |
| Body font | DM Sans via `@remotion/google-fonts` |

Spring config: `{ damping: 12, stiffness: 100, mass: 0.8 }`

---

## Voiceover / Audio

1. Open `voiceover.txt` for the script and production notes
2. Generate MP3 via ElevenLabs (Adam / Rachel voice) or OpenAI TTS (`alloy`)
3. Place output at `public/voiceover.mp3`
4. Uncomment the `<Audio>` line in `src/Composition.tsx`:
   ```tsx
   import { Audio } from "remotion";
   import { staticFile } from "remotion";
   // In MainVideo:
   <Audio src={staticFile("voiceover.mp3")} />
   ```

---

## Data

Dataset: approximate year-end market capitalizations from Bloomberg / CompanyMarketCap.com.
Edit `src/data.ts` to swap in your own dataset.

---

## Acceptance Criteria

- [x] `npx remotion studio` opens without errors
- [x] Total duration: exactly 1800 frames
- [x] Every scene has visible motion
- [x] No Inter / Roboto — uses Fraunces (display) + DM Sans (body)
- [x] One file per scene
- [x] Film grain overlay (SVG feTurbulence, animated per-frame)
- [x] 1-frame white flash between every scene
- [x] Type-checks with `tsc --noEmit`
