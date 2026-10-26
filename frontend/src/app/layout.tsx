import React from "react";
import "./globals.css";

export const metadata = {
  title: "HotWAY — Tối Ưu Tuyến Đường Đô Thị Chặng Cuối Cho Xe Máy | TP.HCM",
  description:
    "Nền tảng tối ưu tuyến đường đô thị chặng cuối cho xe máy tại TP. Hồ Chí Minh: Định tuyến đa tiêu chí Pareto (T1), Lập tuyến đội xe VRPTW khung giờ mềm (T2), và Động cơ đổi đường thích nghi Dynamic Dijkstra (T3).",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400;1,600;1,700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-app text-primary-text antialiased min-h-screen selection:bg-brand-gold-soft selection:text-primary-text font-sans">
        {children}
      </body>
    </html>
  );
}
