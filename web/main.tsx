import React, { useEffect } from "react";
import { createRoot } from "react-dom/client";
import App from "./app/App";
import { navigate, setSessionUserId, usePathname, useSessionUserId } from "./app/session";
import "./app/App.css";
import "./web.css";

const download = "/downloads/leetstreak.zip";

function Brand() {
  return <a className="web-brand" href="/" aria-label="LeetStreak home"><img src="/web-assets/just_logo.png" alt="" /><span>LeetStreak<span className="brand-dot">.</span></span></a>;
}

function Home({ signedIn }: { signedIn: boolean }) {
  return <>
    <section className="web-hero">
      <div className="web-hero-copy">
        <span className="web-eyebrow"><span /> ONE PROBLEM. EVERY DAY.</span>
        <h1>Small steps.<br />Serious <span>streaks.</span></h1>
        <p>Turn your LeetCode practice into a habit that sticks. Track your progress, find your people, and give yourself a reason to come back tomorrow.</p>
        <div className="web-cta-row"><a className="web-button web-button-primary" href={signedIn ? "/dashboard" : "/register"}>{signedIn ? "Go to your dashboard" : "Start your streak"} <span aria-hidden="true">↗</span></a>{!signedIn && <a className="web-button web-button-secondary" href="/login">I have an account</a>}</div>
        <div className="web-hero-note"><span>✦</span> Your public LeetCode handle is all we need to sync.<br />No LeetCode password or session cookies.</div>
      </div>
      <div className="web-preview" aria-label="Illustration of a coding streak, showing sample activity">
        <div className="web-preview-top"><span><span className="web-live-dot" /> THE DAILY PRACTICE</span><span>↗</span></div>
        <div className="web-preview-streak"><img src="/web-assets/main_fire.png" alt="" /><div><strong>Keep it<br />going.</strong><span>YOUR NEXT SOLVE COUNTS</span></div></div>
        <div className="web-preview-calendar">{[3, 1, 4, 2, 5, 3, 4].map((n, i) => <div key={i}><div className="web-preview-bar" style={{height: `${n * 19 + 15}px`}} /><span>{["M", "T", "W", "T", "F", "S", "S"][i]}</span></div>)}</div>
        <div className="web-preview-bottom"><span>A little progress, every day.</span><span>✦</span></div>
        <p className="web-preview-caption">A glimpse of your daily rhythm · sample activity</p>
      </div>
    </section>
    <section className="web-features" id="features" aria-labelledby="features-title">
      <div className="web-section-heading"><span className="web-eyebrow">BUILT FOR THE LONG RUN</span><h2 id="features-title">Make consistency your advantage.</h2></div>
      <div className="web-feature-grid">
        <article><span className="web-feature-icon orange">↗</span><h3>See the habit forming</h3><p>Your daily streak, weekly activity, and solve history in one place. Make every session visible.</p><span className="web-feature-tag">Daily progress</span></article>
        <article><span className="web-feature-icon purple">✦</span><h3>Give every solve weight</h3><p>Earn points for problem difficulty, daily challenges, and consistency. Follow the breakdown behind each solve.</p><span className="web-feature-tag">Thoughtful scoring</span></article>
        <article><span className="web-feature-icon green">◎</span><h3>Bring your coding circle</h3><p>Create a private group, share its invite code, and keep each other moving. Or join the global leaderboard.</p><span className="web-feature-tag">Better together</span></article>
      </div>
    </section>
    <section className="web-get-started"><div><span className="web-eyebrow">LESS SETUP. MORE SOLVING.</span><h2>From your first login<br />to your next milestone.</h2></div><ol><li><span>01</span><div><h3>Create your account</h3><p>Use your email and public LeetCode username.</p></div></li><li><span>02</span><div><h3>Let your progress catch up</h3><p>Sync your activity and see your current streak.</p></div></li><li><span>03</span><div><h3>Show up again tomorrow</h3><p>Solve a problem. Build your streak. Repeat.</p></div></li></ol></section>
    <section className="web-final-cta"><div><h2>Your next streak starts here.</h2><p>Use LeetStreak on the web, or keep it one click away in your browser.</p></div><div className="web-cta-row"><a className="web-button web-button-primary" href={signedIn ? "/dashboard" : "/register"}>{signedIn ? "Open your dashboard ↗" : "Create an account ↗"}</a><a className="web-button web-button-secondary" href={download}>Get the extension ↓</a></div></section>
  </>;
}

function Website() {
  const userId = useSessionUserId();
  const path = usePathname();
  const isHome = path === "/" || path === "/home";
  const isWorkspace = !isHome && userId !== null;
  const authMode = path === "/register" ? "register" : path === "/forgot-password" ? "forgot" : "login";

  useEffect(() => {
    if (userId && !isHome && path !== "/dashboard") navigate("/dashboard", true);
    if (!userId && path === "/dashboard") navigate("/login", true);
  }, [path, userId, isHome]);

  function onRegistered(id: number) {
    setSessionUserId(id);
    navigate("/dashboard", true);
  }
  function onLogout() {
    setSessionUserId(null);
    navigate("/login", true);
  }

  return <div className={`website ${isHome ? "website-home" : isWorkspace ? "website-workspace" : "website-account"}`}>
    <header className="web-nav"><Brand /><nav aria-label="Main navigation">
      {isHome && <a className="web-nav-feature" href="#features">Features</a>}
      <a className="web-nav-download" href={download}>Extension ↓</a>
      {userId ? <>
        <a className="web-nav-dashboard" href="/dashboard" aria-current={isWorkspace ? "page" : undefined}>Dashboard</a>
        <button className="web-signout" onClick={onLogout}>Sign out</button>
      </> : <>
        <a href="/login" aria-current={path === "/login" ? "page" : undefined}>Log in</a>
        <a className="web-button web-button-primary web-nav-start" href="/register">Get started <span aria-hidden="true">↗</span></a>
      </>}
    </nav></header>
    <main>{isHome ? <Home signedIn={userId !== null} /> : <div className={isWorkspace ? "workspace-layout" : "web-app-frame web-auth-frame"}>
      {isWorkspace && <aside className="workspace-sidebar" aria-label="Workspace">
        <span className="workspace-sidebar-label">WORKSPACE</span>
        <nav aria-label="Workspace navigation">
          <a href="#overview"><span aria-hidden="true">◈</span> Overview</a>
          <a href="#leaderboards"><span aria-hidden="true">↗</span> Leaderboards</a>
          <a href="#groups"><span aria-hidden="true">◎</span> Your groups</a>
          <a href="#activity"><span aria-hidden="true">≋</span> Recent solves</a>
          <button onClick={() => window.dispatchEvent(new Event("leetstreak:settings"))}><span aria-hidden="true">⚙</span> Account settings</button>
        </nav>
        <div className="workspace-extension-card"><img src="/web-assets/just_logo.png" alt="" /><strong>Keep your streak close.</strong><p>Use the same account in the browser extension.</p><a href={download}>Get the extension ↓</a></div>
      </aside>}
      <App userId={userId} onRegistered={onRegistered} onLogout={onLogout} authMode={authMode} />
    </div>}</main>
    <footer className="web-footer"><Brand /><span>A little code. A little closer.</span><nav aria-label="Legal"><a href="/privacy">Privacy</a><a href="/terms">Terms</a></nav><p>Independent of LeetCode. Built for your daily practice.</p></footer>
  </div>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><Website /></React.StrictMode>);
