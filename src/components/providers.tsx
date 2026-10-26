"use client";
import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { Toaster } from "react-hot-toast";

const theme = createTheme({
  palette: {
    primary: { main: "#b80d27", dark: "#8f0d23" },
    secondary: { main: "#65111f" },
    text: { primary: "#65111f", secondary: "#6f2a36" },
    background: { default: "#fff8f9", paper: "#fff" },
    warning: { main: "#8c6006", light: "#fff8d9" },
  },
  typography: {
    fontFamily: "Arial, Helvetica, sans-serif",
    button: { textTransform: "none", fontWeight: 700 },
  },
  shape: { borderRadius: 14 },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: {
          minHeight: 46,
          paddingInline: 20,
          "&.MuiButton-contained": {
            backgroundColor: "#b80d27",
            "&:hover": { backgroundColor: "#8f0d23" },
          },
        },
      },
    },
    MuiTextField: {
      defaultProps: { fullWidth: true },
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": { backgroundColor: "#fff8f9" },
          "& fieldset": { borderColor: "#ef163640" },
        },
      },
    },
    MuiDialog: { styleOverrides: { paper: { borderRadius: 20 } } },
    MuiAlert: { styleOverrides: { root: { borderRadius: 14, fontSize: 14 } } },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 20_000,
            retry: false,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      <ThemeProvider theme={theme}>
        {children}
        <Toaster position="top-right" />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
