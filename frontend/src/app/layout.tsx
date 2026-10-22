import React from "react";
import "./globals.css";

export const metadata = {
  title: "HotWAY — Điều Phối & Tối Ưu Tuyến Giao Hàng | Hàng Gòn Quán",
  description:
    "Tuyến giao hàng ngắn nhất để món còn nóng. Hệ thống lập kế hoạch và điều phối tuyến giao hàng cho Hàng Gòn Quán trên mạng lưới đường bộ thực tế.",
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
          href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-app text-primary-text antialiased min-h-screen selection:bg-brand-gold-soft selection:text-primary-text">
        {children}
      </body>
    </html>
  );
}
