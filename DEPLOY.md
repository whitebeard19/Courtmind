# Deploying CourtMind — Railway (backend) + Vercel (frontend)

CourtMind is a monorepo: `backend/` (FastAPI) deploys to **Railway**, `frontend/` (Next.js) deploys to **Vercel**. Both deploy straight from GitHub. Config files (`backend/railway.json`, `backend/nixpacks.toml`, `backend/.python-version`) are already in the repo.

---

## 0. Push the repo to GitHub (once)

From the project root:

```bash
git add -A
git commit -m "CourtMind: deploy-ready (Railway + Vercel)"
# create an empty repo on github.com first, then:
git remote add origin https://github.com/<you>/courtmind.git   # skip if already added
git branch -M main
git push -u origin main
```

> `.env`, `venv/`, `node_modules/`, and `.courtmind_state.json` are gitignored — your keys never leave your machine.

---

## 1. Backend → Railway

1. Go to **railway.app** → **New Project** → **Deploy from GitHub repo** → pick your repo.
2. Open the created service → **Settings**:
   - **Root Directory:** `backend`  ← important (monorepo)
   - Railway auto-detects Nixpacks and reads `backend/railway.json` + `backend/nixpacks.toml` + `backend/.python-version` (pins Python 3.12; installs `libmagic1` for cognee; start command `uvicorn main:app --host 0.0.0.0 --port $PORT`).
3. **Variables** tab → add these (exactly — the app reads them at startup and will crash without them):

   | Variable | Value |
   |---|---|
   | `DASHSCOPE_API_KEY` | your Qwen/DashScope key |
   | `QWEN_MODEL` | `qwen-plus` |
   | `COGNEE_API_KEY` | your Cognee Cloud key |
   | `COGNEE_TENANT_URL` | `https://<your-tenant>.aws.cognee.ai` (no leading space) |
   | `CACHING` | `false` |

4. **Deploy.** Watch the build logs — first build is slow (cognee is a large dependency).
5. **Settings → Networking → Generate Domain.** Copy the public URL, e.g. `https://courtmind-backend-production.up.railway.app`.
6. Verify: open `<that-url>/` in a browser — you should see the JSON health payload (`"reasoning_layer": "Qwen Plus"`), and `<that-url>/docs` for the API.

**If the build/start fails, check:**
- **Wrong Python version** → add a variable `NIXPACKS_PYTHON_VERSION=3.12`.
- **`libmagic` / file-type error at runtime** → confirm `nixpacks.toml` (`aptPkgs = ["libmagic1"]`) is at `backend/nixpacks.toml` and Root Directory is `backend`.
- **App crashes immediately** → a required env var is missing (see the table above).

---

## 2. Frontend → Vercel

1. Go to **vercel.com** → **Add New… → Project** → import the same GitHub repo.
2. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Next.js (auto-detected). Leave build/output defaults.
3. **Environment Variables** → add:

   | Variable | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | your Railway backend URL from step 1.5 (no trailing slash) |

4. **Deploy.** Vercel gives you a URL like `https://courtmind.vercel.app`.
5. Open it — the app should load, list cases from the live backend, and every action should hit Railway.

> CORS is already open on the backend (`allow_origins=["*"]`), so no extra config is needed. Any change to `NEXT_PUBLIC_API_URL` requires a Vercel **redeploy** to take effect (it's baked in at build time).

---

## 3. Post-deploy smoke test

On the live Vercel URL:
1. Create a case.
2. Ingest one document → assertions appear.
3. Ingest a conflicting document → contradiction appears.
4. Query → sourced answer. Generate a brief.

If ingest/query feel slow, that's expected (LLM + cloud memory latency) — see the demo pacing notes in `DEMO.md`.

---

## Notes & caveats

- **Ephemeral filesystem:** Railway resets the container filesystem on each redeploy/restart, so the on-disk `.courtmind_state.json` (case list + contradiction cache) does **not** survive a redeploy. The underlying case memory lives in **Cognee Cloud** and persists; only the lightweight in-process registry resets. For a demo, ingest within the session — fine. (For durable metadata across redeploys, attach a Railway Volume mounted at `backend/` or move the registry into Cognee — not required for the hackathon.)
- **Cold starts:** if the Railway service sleeps (hobby plan), the first request after idle will be slow while it wakes.
- **Cognee budget:** confirm your tenant has budget before a live demo — an exhausted budget degrades query/brief (contradiction detection still works from the cache).
- **Keys:** rotate any key that was ever pasted into a shared chat/log before going public.
