import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "L3 Control Plane · NovaCore LAB",
  description:
    "Operações de uma força de trabalho agêntica. Evidências, decisões e aprendizado com revisão humana.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
