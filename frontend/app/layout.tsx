import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "The Oracle - World Cup 2026 Prediction Agent",
  description:
    "An AI agent that predicts FIFA World Cup 2026 matches: accuracy scoreboard, model battle, and persona banter.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
