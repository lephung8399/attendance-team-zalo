import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Nav } from "@/components/Nav";
import { Providers } from "@/components/Providers";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin", "vietnamese"],
});

export const metadata: Metadata = {
  title: "Điểm danh & Chia đội",
  description: "Quản lý điểm danh và chia đội bóng cân bằng, tích hợp Zalo.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="vi" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <Providers>
          <Nav />
          <main className="mx-auto w-full max-w-5xl flex-1 px-5 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
