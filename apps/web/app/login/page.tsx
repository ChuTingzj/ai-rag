"use client";

import { ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch, type TokenResponse } from "@/lib/api-client";
import { getAccessToken, setAccessToken } from "@/lib/auth-token";

export default function LoginPage() {
  const router = useRouter();
  const emailId = useId();
  const passwordId = useId();
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (getAccessToken()) router.replace("/");
  }, [router]);

  function validateEmail(): boolean {
    const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
    setEmailError(ok ? null : "请输入有效邮箱");
    return ok;
  }

  function validatePassword(): boolean {
    const ok = password.length >= 8;
    setPasswordError(ok ? null : "密码至少 8 位");
    return ok;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    const emailOk = validateEmail();
    const passwordOk = validatePassword();
    if (!emailOk || !passwordOk) {
      if (!emailOk) emailRef.current?.focus();
      else passwordRef.current?.focus();
      return;
    }

    setLoading(true);
    try {
      const token = await apiFetch<TokenResponse>(
        "/auth/login",
        {
          method: "POST",
          body: JSON.stringify({ email: email.trim(), password }),
        },
        false,
      );
      setAccessToken(token.access_token);
      router.push("/");
    } catch (err) {
      const message =
        err instanceof ApiError ? err.detail ?? err.message : "登录失败，请重试";
      setSubmitError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative grid min-h-screen place-items-center overflow-hidden bg-background p-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_#EEF2FF_0%,_transparent_55%)]" />
      <div className="pointer-events-none absolute -left-24 top-24 size-72 rounded-full bg-primary/10 blur-3xl" />
      <Card className="relative w-full max-w-[400px] shadow-[0_1px_2px_rgb(15_23_42_/_0.06)] animate-in fade-in slide-in-from-bottom-1 duration-300">
        <CardHeader className="items-center text-center">
          <div className="mb-1 flex size-12 items-center justify-center rounded-lg bg-sidebar text-sidebar-foreground">
            <ShieldCheck className="size-7 text-primary" aria-hidden="true" />
          </div>
          <CardTitle className="text-2xl font-extrabold tracking-tight">
            企业知识助手
          </CardTitle>
          <CardDescription>登录以访问知识库与智能问答</CardDescription>
        </CardHeader>
        <CardContent>
          {submitError ? (
            <div
              className="mb-4 rounded-lg bg-destructive/12 px-3 py-2 text-sm text-destructive"
              role="alert"
            >
              {submitError}
            </div>
          ) : null}

          <form onSubmit={onSubmit} noValidate className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor={emailId}>邮箱</Label>
              <Input
                ref={emailRef}
                id={emailId}
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
                className="h-10 bg-background"
                value={email}
                onChange={(ev) => setEmail(ev.target.value)}
                onBlur={validateEmail}
                aria-invalid={emailError ? true : undefined}
                aria-describedby={emailError ? `${emailId}-err` : undefined}
              />
              {emailError ? (
                <p id={`${emailId}-err`} className="text-xs text-destructive">
                  {emailError}
                </p>
              ) : null}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor={passwordId}>密码</Label>
              <Input
                ref={passwordRef}
                id={passwordId}
                type="password"
                autoComplete="current-password"
                placeholder="至少 8 位"
                className="h-10 bg-background"
                value={password}
                onChange={(ev) => setPassword(ev.target.value)}
                onBlur={validatePassword}
                aria-invalid={passwordError ? true : undefined}
                aria-describedby={passwordError ? `${passwordId}-err` : undefined}
              />
              {passwordError ? (
                <p id={`${passwordId}-err`} className="text-xs text-destructive">
                  {passwordError}
                </p>
              ) : null}
            </div>

            <Button type="submit" className="h-11 w-full" disabled={loading}>
              {loading ? "登录中…" : "登录"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
