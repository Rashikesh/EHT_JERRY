// src/app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Industrial Safety Monitor",
  description: "Digital Permit Intelligence Agent",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="m-0 p-0 bg-[#0f172a] overflow-hidden">
        {children}
      </body>
    </html>
  );
}