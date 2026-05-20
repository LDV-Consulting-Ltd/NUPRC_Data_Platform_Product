import ConsoleSidebar from "@/components/console/ConsoleSidebar";
import ConsoleTopBar from "@/components/console/ConsoleTopBar";

export default function ConsoleLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen w-full">
      <ConsoleSidebar />
      <div className="flex flex-1 flex-col min-w-0">
        <ConsoleTopBar />
        <main className="flex-1 w-full min-w-0 p-6 bg-[#f4f7fb]">{children}</main>
      </div>
    </div>
  );
}
