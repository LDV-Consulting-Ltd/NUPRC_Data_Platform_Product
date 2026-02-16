import type { Metadata } from "next";
import "./globals.css";
import V2Sidebar from "./components/V2Sidebar";
import QueryProvider from "./QueryProvider";

export const metadata: Metadata = {
  title: "LDV Data Console — Energy Regulator Tenant Data Fabric",
  description: "LDV Data Console - Energy Regulator Tenant Data Fabric",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <script src="https://cdn.tailwindcss.com" />
        <script
          dangerouslySetInnerHTML={{
            __html: "tailwind.config = { theme: { extend: { colors: { 'ldv-green': '#0B6B3A', 'ldv-gold': '#C9A227', 'ldv-blue': '#2563EB', 'ldv-amber': '#F59E0B', 'ldv-red': '#DC2626' } } } } }",
          }}
        />
      </head>
      <body>
        <QueryProvider>
          <div className="min-h-screen flex">
            <V2Sidebar />
            <main className="flex-1 min-w-0 flex flex-col">
              {children}
            </main>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
