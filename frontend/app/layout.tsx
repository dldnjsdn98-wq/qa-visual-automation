import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Game QA Workspace",
  description: "Game Multilingual QA Visual Automation System",
};
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="ko"><body>{children}</body></html>;
}

