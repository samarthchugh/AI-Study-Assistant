"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
} from "firebase/auth";
import { firebaseAuth, googleProvider, githubProvider } from "./firebase";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface AuthContextValue {
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  loginWithGitHub: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function exchangeFirebaseToken(idToken: string): Promise<string> {
  const res = await fetch(`${BASE_URL}/auth/firebase`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Auth failed" }));
    throw new Error(err.detail ?? "Authentication failed");
  }
  const data = await res.json();
  return data.access_token;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("access_token");
    if (stored) setToken(stored);
    setIsLoading(false);
  }, []);

  const storeToken = (t: string) => {
    localStorage.setItem("access_token", t);
    setToken(t);
  };

  const login = async (email: string, password: string) => {
    const result = await signInWithEmailAndPassword(firebaseAuth, email, password);
    const idToken = await result.user.getIdToken();
    const jwt = await exchangeFirebaseToken(idToken);
    storeToken(jwt);
  };

  const signup = async (email: string, password: string) => {
    const result = await createUserWithEmailAndPassword(firebaseAuth, email, password);
    const idToken = await result.user.getIdToken();
    const jwt = await exchangeFirebaseToken(idToken);
    storeToken(jwt);
  };

  const loginWithGoogle = async () => {
    const result = await signInWithPopup(firebaseAuth, googleProvider);
    const idToken = await result.user.getIdToken();
    const jwt = await exchangeFirebaseToken(idToken);
    storeToken(jwt);
  };

  const loginWithGitHub = async () => {
    const result = await signInWithPopup(firebaseAuth, githubProvider);
    const idToken = await result.user.getIdToken();
    const jwt = await exchangeFirebaseToken(idToken);
    storeToken(jwt);
  };

  const logout = async () => {
    await signOut(firebaseAuth);
    localStorage.removeItem("access_token");
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, isLoading, login, signup, loginWithGoogle, loginWithGitHub, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
