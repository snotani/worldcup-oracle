// Small hand-rolled inline SVG icon set so the dashboard ships with zero icon
// dependencies (and no build-time network fetches). Stroke-based, 1.8px, 24x24.

type P = { size?: number; className?: string; strokeWidth?: number };

const base = (size: number) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
});

export const IconTrophy = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="M6 4h12v3a6 6 0 0 1-12 0V4Z" />
    <path d="M6 5H3v2a3 3 0 0 0 3 3M18 5h3v2a3 3 0 0 1-3 3" />
    <path d="M9 18h6M10 18l.5-3h3l.5 3M8 21h8" />
  </svg>
);

export const IconTarget = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="5" />
    <circle cx="12" cy="12" r="1.5" />
  </svg>
);

export const IconActivity = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="M3 12h4l3 8 4-16 3 8h4" />
  </svg>
);

export const IconBrain = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="M9.5 3A2.5 2.5 0 0 0 7 5.5v.2A2.8 2.8 0 0 0 5 8.4 2.7 2.7 0 0 0 5 13a2.7 2.7 0 0 0 2 4.5 2.5 2.5 0 0 0 5 .5V5.5A2.5 2.5 0 0 0 9.5 3Z" />
    <path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v.2a2.8 2.8 0 0 1 2 2.7 2.7 2.7 0 0 1 0 4.6 2.7 2.7 0 0 1-2 4.5 2.5 2.5 0 0 1-5 .5" />
  </svg>
);

export const IconFlame = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="M12 3c1 3-1 4-1 6a3 3 0 0 0 5 2c1 2 1 3 1 4a5 5 0 0 1-10 0c0-3 2-5 3-7 .5 1 1 1.5 2 2-.5-3 0-5 0-7Z" />
  </svg>
);

export const IconChevron = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="m6 9 6 6 6-6" />
  </svg>
);

export const IconCheck = ({ size = 18, className, strokeWidth = 2.2 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="m5 12 5 5L20 7" />
  </svg>
);

export const IconX = ({ size = 18, className, strokeWidth = 2.2 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="M6 6 18 18M18 6 6 18" />
  </svg>
);

export const IconClock = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </svg>
);

export const IconPin = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="M12 21s-6-5.2-6-10a6 6 0 0 1 12 0c0 4.8-6 10-6 10Z" />
    <circle cx="12" cy="11" r="2.2" />
  </svg>
);

export const IconBolt = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" />
  </svg>
);

export const IconDatabase = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <ellipse cx="12" cy="5" rx="8" ry="3" />
    <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
  </svg>
);

export const IconScale = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="M12 3v18M7 21h10M5 7l14-2" />
    <path d="M5 7 2.5 13a3 3 0 0 0 5 0L5 7ZM19 5l-2.5 6a3 3 0 0 0 5 0L19 5Z" />
  </svg>
);

export const IconSparkles = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <path d="M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3Z" />
    <path d="M18 14l.8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14Z" />
  </svg>
);

export const IconGitBranch = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <circle cx="6" cy="5" r="2" />
    <circle cx="6" cy="19" r="2" />
    <circle cx="18" cy="7" r="2" />
    <path d="M6 7v10M18 9a6 6 0 0 1-6 6H8" />
  </svg>
);

export const IconUsers = ({ size = 18, className, strokeWidth = 1.8 }: P) => (
  <svg {...base(size)} strokeWidth={strokeWidth} className={className}>
    <circle cx="9" cy="8" r="3" />
    <path d="M3 20a6 6 0 0 1 12 0M16 5.5a3 3 0 0 1 0 5M21 20a6 6 0 0 0-4-5.6" />
  </svg>
);
