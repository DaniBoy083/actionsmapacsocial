"use client";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useMediaQuery } from "@mui/material";
import {
  FiArrowUpRight,
  FiChevronLeft,
  FiFilePlus,
  FiGrid,
  FiLogOut,
  FiMapPin,
  FiMenu,
  FiServer,
} from "react-icons/fi";
import toast from "react-hot-toast";
import { api, errorMessage, type Session } from "@/lib/api";
import { SessionContext } from "@/components/session-context";

export function AppShell({
  session,
  children,
}: {
  session: Session;
  children: React.ReactNode;
}) {
  const smallScreen = useMediaQuery("(max-width:900px)");
  const [menuChoice, setCollapsed] = useState<boolean | null>(null);
  const collapsed = menuChoice ?? smallScreen;
  const [leaving, setLeaving] = useState(false);
  const sidebar = useRef<HTMLElement>(null);
  const path = usePathname();
  const router = useRouter();
  const queries = useQueryClient();
  const links = [
    { href: "/dashboard", label: "Visão geral", icon: FiGrid },
    { href: "/acoes", label: "Ações institucionais", icon: FiMapPin },
    { href: "/mapa-acoes", label: "Mapa de ações", icon: FiMapPin },
    { href: "/importacoes", label: "Importar dados", icon: FiFilePlus },
    ...(session.equipe === "tecnologia"
      ? [
          {
            href: "/tecnologia/conexao",
            label: "Conexão e integrações",
            icon: FiServer,
          },
        ]
      : []),
  ];
  useEffect(() => {
    const footer = document.querySelector(".institutional-footer");
    const observer = new IntersectionObserver(
      ([entry]) =>
        sidebar.current?.style.setProperty(
          "--panel-footer-overlap",
          `${entry.isIntersecting ? entry.intersectionRect.height : 0}px`,
        ),
      { threshold: [0, 0.25, 0.5, 0.75, 1] },
    );
    if (footer) observer.observe(footer);
    return () => observer.disconnect();
  }, []);
  async function logout() {
    setLeaving(true);
    try {
      await api.post(
        "/auth/logout",
        {},
        { headers: { "X-CSRF-Token": session.csrf_token } },
      );
      queries.clear();
      router.replace("/login");
      router.refresh();
    } catch (error) {
      toast.error(errorMessage(error));
      setLeaving(false);
    }
  }
  const agenda = /^https?:\/\//.test(session.agenda_url)
    ? session.agenda_url
    : null;
  return (
    <SessionContext value={session}>
      <div className={`app-frame ${collapsed ? "is-collapsed" : ""}`}>
        <aside
          ref={sidebar}
          className={`sidebar ${collapsed ? "collapsed" : ""}`}
          aria-label="Navegação principal"
        >
          <div className="sidebar-top">
            {!collapsed && (
              <>
                <Image
                  src="/logo-ac-social.png"
                  unoptimized
                  alt="AC Social"
                  width={48}
                  height={48}
                  style={{ borderRadius: 12 }}
                />
                <div className="hide-collapsed">
                  <div className="sidebar-title">AC Actions Map</div>
                  <small>GESTÃO INSTITUCIONAL</small>
                </div>
              </>
            )}
            <button
              className="sidebar-toggle"
              aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
              aria-expanded={!collapsed}
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? <FiMenu /> : <FiChevronLeft />}
            </button>
          </div>
          <nav className="sidebar-nav">
            <p className="eyebrow hide-collapsed">Módulos do sistema</p>
            {links.map((item) => (
              <Link
                key={item.href}
                className="nav-item"
                href={item.href}
                title={item.label}
                aria-label={item.label}
                aria-current={
                  path === item.href ||
                  (item.href === "/acoes" && path.startsWith("/acoes/"))
                    ? "page"
                    : undefined
                }
                onClick={() => {
                  if (window.innerWidth < 640) setCollapsed(true);
                }}
              >
                <item.icon />
                <span className="hide-collapsed">{item.label}</span>
              </Link>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="session-card hide-collapsed">
              <small>SESSÃO INSTITUCIONAL</small>
              <strong>{session.nome}</strong>
              <small>
                Administrativo ·{" "}
                {session.equipe === "tecnologia"
                  ? "Tecnologia"
                  : "Administração"}
              </small>
            </div>
            {agenda && (
              <a
                className="nav-item"
                href={agenda}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Abrir Agenda Digital"
              >
                <FiArrowUpRight />
                <span className="hide-collapsed">Agenda Digital</span>
              </a>
            )}
            <button
              className="nav-item"
              onClick={logout}
              disabled={leaving}
              aria-label="Sair"
            >
              <FiLogOut />
              <span className="hide-collapsed">
                {leaving ? "Saindo…" : "Sair"}
              </span>
            </button>
          </div>
        </aside>
        <main id="conteudo" className="main-area">
          <header className="topbar">
            <span className="eyebrow">AC Social / Gestão de ações</span>
            <span className="muted">Acesso restrito</span>
          </header>
          {children}
        </main>
      </div>
    </SessionContext>
  );
}
