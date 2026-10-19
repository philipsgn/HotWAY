import React from "react";
import "./globals.css";

export const metadata = {
  title: "HotWAY - Quán Bánh Canh Gà Hàng Gòn",
  description: "Hệ thống điều phối giao hàng tối ưu nhiệt độ bằng Học Tăng Cường (Reinforcement Learning) tại Hàng Gòn, Long Khánh",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body className="bg-slate-50 text-slate-900 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
