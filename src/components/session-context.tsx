"use client";
import { createContext, useContext } from "react";
import type { Session } from "@/lib/api";
export const SessionContext = createContext<Session | null>(null);
export function useSession() {
  const value = useContext(SessionContext);
  if (!value) throw new Error("Sessão indisponível.");
  return value;
}
