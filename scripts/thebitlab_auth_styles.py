"""Shared CSS for TheBitLab authentication and administration pages."""

AUTH_PAGE_CSS = """
:root {
  --bg: #fafafa;
  --ink: #1a1a1e;
  --soft: #5a5a62;
  --faint: #7a7a82;
  --card: #ffffff;
  --line: #e6e6ea;
  --accent: #1a1a1e;
  --accent-inverted: #ffffff;
  --google: #4285F4;
  --ok: #2e7d32;
  --mono: "Cascadia Code", "JetBrains Mono", "Fira Code", Consolas, monospace;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  min-height: 100vh;
}
.topNav {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: .35rem;
  padding: .65rem clamp(1rem, 3vw, 3rem);
  border-bottom: 1px solid rgba(26, 26, 30, .12);
  background: rgba(255, 255, 255, .94);
  backdrop-filter: blur(10px);
}
.topNavBrand {
  display: grid;
  place-items: center;
  width: 2.35rem;
  height: 2.35rem;
  margin-right: .25rem;
  border: 1px solid rgba(26, 26, 30, .14);
  border-radius: .7rem;
  background: #ffffff;
  overflow: hidden;
}
.topNavBrand img { width: 100%; height: 100%; object-fit: contain; }
.topNavTitle { font-weight: 650; font-size: .95rem; }
.topNavTitle span { color: var(--soft); font-weight: 400; margin-left: .5rem; }
main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 2rem clamp(1rem, 3vw, 3rem);
}
h1 { font-size: 1.3rem; margin-bottom: 1.25rem; letter-spacing: -.02em; }
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 1rem;
  padding: 1.25rem;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.04);
}
.card h2 {
  font-size: 1.05rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: .5rem;
}
.badge {
  font-size: .7rem;
  padding: .15rem .45rem;
  border-radius: 999px;
  background: var(--bg);
  color: var(--soft);
  border: 1px solid var(--line);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.25rem;
  align-items: start;
}
table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th, td { text-align: left; padding: .55rem 0; border-bottom: 1px solid var(--line); }
th {
  color: var(--soft);
  font-weight: 500;
  font-size: .8rem;
  text-transform: uppercase;
  letter-spacing: .03em;
}
.mono { font-family: var(--mono); font-size: .85rem; }
form.row {
  display: flex;
  gap: .5rem;
  flex-wrap: wrap;
  margin-top: 1rem;
}
input, select {
  padding: .55rem .7rem;
  border: 1px solid var(--line);
  border-radius: .5rem;
  background: #fff;
  color: var(--ink);
  font: inherit;
}
input.small { width: 8rem; }
button, .btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: .5rem;
  padding: .55rem 1rem;
  border-radius: .5rem;
  border: none;
  background: var(--accent);
  color: var(--accent-inverted);
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: filter .15s;
}
button:hover, .btn:hover { filter: brightness(0.95); }
button.secondary { background: #fff; color: var(--ink); border: 1px solid var(--line); }
button.ok { background: var(--ok); }
.pending-item { padding: .9rem 0; border-bottom: 1px solid var(--line); }
.pending-item:last-child { border-bottom: none; }
.pending-item .email { font-weight: 500; font-size: .9rem; margin-bottom: .35rem; }
.pending-item .meta { color: var(--soft); font-size: .8rem; margin-bottom: .6rem; }
.hint { color: var(--faint); font-size: .8rem; margin-top: .75rem; }
.login-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 1rem;
}
.login-card {
  width: min(420px, 100%);
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 1.25rem;
  padding: 2.5rem;
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.06);
  text-align: center;
}
.login-brand {
  width: 4rem;
  height: 4rem;
  margin: 0 auto 1.25rem;
  border-radius: 1rem;
  overflow: hidden;
}
.login-brand img { width: 100%; height: 100%; object-fit: contain; }
.login-card h1 { font-size: 1.45rem; font-weight: 650; margin-bottom: .35rem; }
.login-card p.sub { color: var(--soft); font-size: .95rem; margin-bottom: 1.75rem; }
.login-card .btn-google {
  width: 100%;
  padding: .85rem 1rem;
  border-radius: .65rem;
  background: var(--google);
  color: #fff;
}
.login-card .teacher {
  margin-top: 1.25rem;
  font-size: .85rem;
  color: var(--faint);
}
.login-card .teacher a { color: var(--ink); text-underline-offset: .15rem; }
.account-card { max-width: 520px; margin: 0 auto; text-align: center; padding-top: 3rem; }
.account-card h1 { font-size: 1.45rem; margin-bottom: .75rem; }
.account-card p { color: var(--soft); margin-bottom: 1.5rem; }
.account-card .btn { margin-top: .25rem; }
"""
