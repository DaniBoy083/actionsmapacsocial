import type { Metadata } from "next";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v16-appRouter";
import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "AC Actions Map — AC Social",
    template: "%s | AC Actions Map",
  },
  description: "Gestão institucional de ações e beneficiários da AC Social.",
  robots: { index: false, follow: false },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>
        <AppRouterCacheProvider options={{ enableCssLayer: true }}>
          <Providers>
            <a className="skip-link" href="#conteudo">
              Ir para o conteúdo
            </a>
            {children}
            <footer className="institutional-footer">
              <strong>AC SOCIAL | AC ACTIONS MAP</strong>
              <span>
                Ambiente institucional para gestão de ações e registros gerais
                de beneficiários.
              </span>
            </footer>
          </Providers>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
