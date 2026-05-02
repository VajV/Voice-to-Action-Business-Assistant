import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Voice-to-Action Business Assistant",
  description: "Turn meeting audio into summaries, decisions, action items, and Slack updates."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
