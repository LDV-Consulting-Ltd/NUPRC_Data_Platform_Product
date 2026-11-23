import type { Metadata } from "next";
import "./globals.css";
import "./styles/console.css";
import QueryProvider from "./QueryProvider";
import AppChrome from "./components/console/AppChrome";

export const metadata: Metadata = {
  title: "LDV Data Console · NUPRC",
  description:
    "LDV Consulting’s upstream petroleum data product, built from published NUPRC reports. Not an official NUPRC application.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <AppChrome>{children}</AppChrome>
        </QueryProvider>
      </body>
    </html>
  );
}
