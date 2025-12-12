import type { Metadata } from "next";
import "./globals.css";
import type { PropsWithChildren } from "react";
import LayoutDefault from "@/components/Layouts/LayoutDefault";

export const metadata: Metadata = {
  title: "Synphora App",
  description: "Made by samanwirst",
};

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en">
      <body>
        <LayoutDefault>{children}</LayoutDefault>
      </body>
    </html>
  );
}
