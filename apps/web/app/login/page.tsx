"use client";

import { ShieldCheck } from "@phosphor-icons/react";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";

import ui from "@/components/ui.module.css";
import { ApiError, apiFetch, type TokenResponse } from "@/lib/api-client";
import { getAccessToken, setAccessToken } from "@/lib/auth-token";

import styles from "./login.module.css";

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
    <div className={styles.page}>
      <div className={styles.cardWrap}>
        <div className={`${ui.card} ${styles.card}`}>
          <header className={styles.header}>
            <ShieldCheck size={32} weight="regular" aria-hidden="true" />
            <h1 className={styles.title}>企业知识助手</h1>
            <p className={styles.subtitle}>登录以访问知识库与智能问答</p>
          </header>

          {submitError ? (
            <div className={ui.errorSummary} role="alert">
              {submitError}
            </div>
          ) : null}

          <form onSubmit={onSubmit} noValidate>
            <div className={ui.field}>
              <label className={ui.label} htmlFor={emailId}>
                邮箱
              </label>
              <input
                ref={emailRef}
                id={emailId}
                className={ui.input}
                type="email"
                autoComplete="email"
                value={email}
                onChange={(ev) => setEmail(ev.target.value)}
                onBlur={validateEmail}
                aria-invalid={emailError ? true : undefined}
                aria-describedby={emailError ? `${emailId}-err` : undefined}
              />
              {emailError ? (
                <p id={`${emailId}-err`} className={styles.fieldError}>
                  {emailError}
                </p>
              ) : null}
            </div>

            <div className={ui.field}>
              <label className={ui.label} htmlFor={passwordId}>
                密码
              </label>
              <input
                ref={passwordRef}
                id={passwordId}
                className={ui.input}
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(ev) => setPassword(ev.target.value)}
                onBlur={validatePassword}
                aria-invalid={passwordError ? true : undefined}
                aria-describedby={passwordError ? `${passwordId}-err` : undefined}
              />
              {passwordError ? (
                <p id={`${passwordId}-err`} className={styles.fieldError}>
                  {passwordError}
                </p>
              ) : null}
            </div>

            <button
              type="submit"
              className={`${ui.btnPrimary} ${styles.submit}`}
              disabled={loading}
            >
              {loading ? "登录中…" : "登录"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
