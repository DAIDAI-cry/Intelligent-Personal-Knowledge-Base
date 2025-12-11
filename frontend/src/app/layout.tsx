"use client";
import type React from "react";

import "./globals.css";
import { ThemeProvider } from "next-themes";
import { Button } from "@/components/ui/button";
import { useContext, useEffect, useRef } from "react";
import { Player } from "@lordicon/react";
import { AuthContext, AuthProvider } from "./contexts/AuthContext";
import { useRouter } from "next/navigation";

import axios from "axios";
import { toast, Toaster } from "sonner";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const playerRef = useRef<Player>(null);
  
  useEffect(() => {
    playerRef.current?.playFromBeginning();
  }, []);
  
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <LayoutContent>{children}</LayoutContent>
        </AuthProvider>
      </body>
    </html>
  );
}

// Separated into a child component to ensure it has access to the initialized context
function LayoutContent({ children }: { children: React.ReactNode }) {
  const { isLoggedIn, setIsLoggedIn } = useContext(AuthContext);
  const router =useRouter();
  // Check localStorage on mount to synchronize the login state
  useEffect(() => {
    const storedLoginState = localStorage.getItem("isLoggedIn");
    const accessToken = localStorage.getItem("accessToken");
    
    if (storedLoginState === "true" && accessToken) {
      setIsLoggedIn(true);
    }
  }, [setIsLoggedIn]);
  
  const handleLogout = async () => {
    try {
      const accessToken = localStorage.getItem("accessToken");
      const refreshToken = localStorage.getItem("refreshToken");

      if (!accessToken || !refreshToken) {
        toast.warning("未找到活跃会话。");
        return;
      }

      const response = await axios.post(
        `http://localhost:8000/logout/`,
        { refresh: refreshToken },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`, 
          },
          withCredentials: true
        }
      );

      if (response.status === 205) {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("isLoggedIn");
        setIsLoggedIn(false);
        toast.success("已成功退出登录！");
        window.location.href = "/";
      } else {
        const errorData = await response.data
        toast.error(errorData.message || "退出登录失败。");
      }
    } catch (error) {
      console.error("Error during logout:", error);
      toast.error("退出登录时发生错误。");
    }
  };

  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      <div className="flex min-h-screen flex-col">
        <header className="sticky top-0 z-40 border-b bg-background">
          <div className="container flex h-16 items-center justify-between py-4">
            <div className="flex items-center gap-2">
            </div>
            <nav className="flex gap-6"></nav>
            {isLoggedIn && (
              <div className="flex items-center gap-4">
                <Button onClick={handleLogout}>退出登录</Button>
              </div>
            )}
          </div>
        </header>
        <main className="flex-1 bg-muted/40 full-page-bg">
        <Toaster position="top-center"/>
          {children}
        </main>

      </div>
    </ThemeProvider>
  );
}