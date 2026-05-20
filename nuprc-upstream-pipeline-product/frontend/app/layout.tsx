import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "PetroCore — Upstream Governance & Intelligence Platform",
  description:
    "PetroCore: automated acquisition, standardization, warehousing, governance, and analytics for Nigerian upstream regulatory intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script src="https://cdn.tailwindcss.com" />
        <script
          dangerouslySetInnerHTML={{
            __html:
              "tailwind.config = { theme: { extend: { colors: { 'ldv-green': '#0B6B3A', 'ldv-gold': '#C9A227', 'ldv-blue': '#2563EB', 'navy-900': '#0f2744', 'teal-500': '#14b8a6' } } } } }",
          }}
        />
      </head>
      <body suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
