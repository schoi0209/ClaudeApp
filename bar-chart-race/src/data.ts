export interface DataPoint {
  name: string;
  value: number; // market cap in billions USD
}

export interface YearData {
  year: number;
  data: DataPoint[];
}

export const TRACKED_COMPANIES = [
  "Apple",
  "Microsoft",
  "Google",
  "Amazon",
  "Meta",
  "Tesla",
  "NVIDIA",
  "Berkshire",
  "TSMC",
  "Samsung",
] as const;

export type CompanyName = (typeof TRACKED_COMPANIES)[number];

// Distinct, restrained palette — one accent red for Tesla, others in disciplined hues
export const COMPANY_COLORS: Record<CompanyName, string> = {
  Apple: "hsl(0, 0%, 14%)",
  Microsoft: "hsl(207, 100%, 40%)",
  Google: "hsl(143, 52%, 38%)",
  Amazon: "hsl(28, 95%, 50%)",
  Meta: "hsl(214, 85%, 52%)",
  Tesla: "hsl(3, 79%, 54%)", // accent red
  NVIDIA: "hsl(97, 72%, 33%)",
  Berkshire: "hsl(32, 48%, 38%)",
  TSMC: "hsl(192, 68%, 38%)",
  Samsung: "hsl(232, 85%, 46%)",
};

// Market cap data in billions USD (approximate year-end values)
export const YEARLY_DATA: YearData[] = [
  {
    year: 2015,
    data: [
      { name: "Apple", value: 724 },
      { name: "Microsoft", value: 358 },
      { name: "Google", value: 527 },
      { name: "Amazon", value: 318 },
      { name: "Meta", value: 296 },
      { name: "Tesla", value: 30 },
      { name: "NVIDIA", value: 18 },
      { name: "Berkshire", value: 320 },
      { name: "TSMC", value: 120 },
      { name: "Samsung", value: 185 },
    ],
  },
  {
    year: 2016,
    data: [
      { name: "Apple", value: 617 },
      { name: "Microsoft", value: 482 },
      { name: "Google", value: 556 },
      { name: "Amazon", value: 356 },
      { name: "Meta", value: 332 },
      { name: "Tesla", value: 35 },
      { name: "NVIDIA", value: 57 },
      { name: "Berkshire", value: 410 },
      { name: "TSMC", value: 140 },
      { name: "Samsung", value: 220 },
    ],
  },
  {
    year: 2017,
    data: [
      { name: "Apple", value: 900 },
      { name: "Microsoft", value: 660 },
      { name: "Google", value: 730 },
      { name: "Amazon", value: 563 },
      { name: "Meta", value: 513 },
      { name: "Tesla", value: 62 },
      { name: "NVIDIA", value: 120 },
      { name: "Berkshire", value: 492 },
      { name: "TSMC", value: 185 },
      { name: "Samsung", value: 300 },
    ],
  },
  {
    year: 2018,
    data: [
      { name: "Apple", value: 746 },
      { name: "Microsoft", value: 780 },
      { name: "Google", value: 723 },
      { name: "Amazon", value: 734 },
      { name: "Meta", value: 374 },
      { name: "Tesla", value: 58 },
      { name: "NVIDIA", value: 97 },
      { name: "Berkshire", value: 497 },
      { name: "TSMC", value: 200 },
      { name: "Samsung", value: 268 },
    ],
  },
  {
    year: 2019,
    data: [
      { name: "Apple", value: 1305 },
      { name: "Microsoft", value: 1200 },
      { name: "Google", value: 920 },
      { name: "Amazon", value: 916 },
      { name: "Meta", value: 586 },
      { name: "Tesla", value: 77 },
      { name: "NVIDIA", value: 145 },
      { name: "Berkshire", value: 554 },
      { name: "TSMC", value: 300 },
      { name: "Samsung", value: 260 },
    ],
  },
  {
    year: 2020,
    data: [
      { name: "Apple", value: 2250 },
      { name: "Microsoft", value: 1680 },
      { name: "Google", value: 1185 },
      { name: "Amazon", value: 1634 },
      { name: "Meta", value: 756 },
      { name: "Tesla", value: 669 },
      { name: "NVIDIA", value: 323 },
      { name: "Berkshire", value: 540 },
      { name: "TSMC", value: 449 },
      { name: "Samsung", value: 370 },
    ],
  },
  {
    year: 2021,
    data: [
      { name: "Apple", value: 2900 },
      { name: "Microsoft", value: 2530 },
      { name: "Google", value: 1920 },
      { name: "Amazon", value: 1740 },
      { name: "Meta", value: 900 },
      { name: "Tesla", value: 1060 },
      { name: "NVIDIA", value: 735 },
      { name: "Berkshire", value: 670 },
      { name: "TSMC", value: 590 },
      { name: "Samsung", value: 430 },
    ],
  },
  {
    year: 2022,
    data: [
      { name: "Apple", value: 2066 },
      { name: "Microsoft", value: 1787 },
      { name: "Google", value: 1144 },
      { name: "Amazon", value: 857 },
      { name: "Meta", value: 319 },
      { name: "Tesla", value: 389 },
      { name: "NVIDIA", value: 360 },
      { name: "Berkshire", value: 676 },
      { name: "TSMC", value: 430 },
      { name: "Samsung", value: 295 },
    ],
  },
  {
    year: 2023,
    data: [
      { name: "Apple", value: 3046 },
      { name: "Microsoft", value: 2795 },
      { name: "Google", value: 1732 },
      { name: "Amazon", value: 1568 },
      { name: "Meta", value: 912 },
      { name: "Tesla", value: 791 },
      { name: "NVIDIA", value: 1224 },
      { name: "Berkshire", value: 783 },
      { name: "TSMC", value: 584 },
      { name: "Samsung", value: 350 },
    ],
  },
  {
    year: 2024,
    data: [
      { name: "Apple", value: 3200 },
      { name: "Microsoft", value: 3100 },
      { name: "Google", value: 2100 },
      { name: "Amazon", value: 1900 },
      { name: "Meta", value: 1400 },
      { name: "Tesla", value: 700 },
      { name: "NVIDIA", value: 3350 }, // NVIDIA peaks to #1 in 2024
      { name: "Berkshire", value: 950 },
      { name: "TSMC", value: 900 },
      { name: "Samsung", value: 300 },
    ],
  },
];

export function formatValue(value: number): string {
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}T`;
  }
  return `$${Math.round(value)}B`;
}

export function getInterpolatedData(frame: number, totalFrames: number): DataPoint[] {
  const NUM_TRANSITIONS = 9;
  const rawProgress = Math.min((frame / (totalFrames - 1)) * NUM_TRANSITIONS, NUM_TRANSITIONS);
  const fromIdx = Math.min(Math.floor(rawProgress), 8);
  const toIdx = Math.min(fromIdx + 1, 9);
  const t = rawProgress - fromIdx;
  const easedT = easeInOutCubic(t);

  return TRACKED_COMPANIES.map((name) => {
    const fromVal = YEARLY_DATA[fromIdx].data.find((d) => d.name === name)?.value ?? 0;
    const toVal = YEARLY_DATA[toIdx].data.find((d) => d.name === name)?.value ?? 0;
    return { name, value: fromVal + (toVal - fromVal) * easedT };
  });
}

export function getDisplayYear(frame: number, totalFrames: number): number {
  const NUM_TRANSITIONS = 9;
  const rawProgress = Math.min((frame / (totalFrames - 1)) * NUM_TRANSITIONS, NUM_TRANSITIONS);
  return Math.round(2015 + rawProgress);
}

function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}
