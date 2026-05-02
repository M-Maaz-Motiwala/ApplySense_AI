import "./globals.css";
import Link from "next/link";
import { getToken, logout } from "../lib/auth";

export const metadata = {
  title: "ApplySense AI",
  description: "AI-powered automated job application platform",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const token = await getToken();

  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 font-sans min-h-screen">
        <nav className="fixed top-0 left-0 right-0 h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 z-50 flex items-center justify-between px-6">
          <div className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-indigo-600 to-blue-500 bg-clip-text text-transparent">
            <Link href="/">ApplySense AI</Link>
          </div>
          <div className="flex items-center gap-6">
            <Link href="/jobs" className="text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Jobs</Link>
            <Link href="/applications" className="text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Applications</Link>
            
            {token ? (
              <div className="flex items-center gap-4 border-l border-slate-200 pl-4 ml-2">
                <Link href="/dashboard" className="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 hover:bg-indigo-200 transition-colors" title="Dashboard">
                  👤
                </Link>
                <form action={async () => { "use server"; await logout(); }}>
                  <button type="submit" className="text-sm font-semibold text-slate-500 hover:text-red-600 transition-colors">
                    Logout
                  </button>
                </form>
              </div>
            ) : (
              <Link href="/auth/login" className="bg-white border border-slate-200 shadow-sm hover:bg-slate-50 text-slate-900 text-sm font-semibold py-1.5 px-4 rounded-md transition-all">
                Login
              </Link>
            )}
          </div>
        </nav>
        <div className="pt-16 max-w-6xl mx-auto p-6">
          {children}
        </div>
      </body>
    </html>
  );
}
