import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Emotion Classifier",
  description: "Type a sentence and see which emotion it maps to.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
