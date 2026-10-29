# Emotion Classifier

A small web app that reads a sentence and predicts the emotion behind it —
one of six: **sadness, joy, love, anger, fear, surprise**.

**Live:**

- App — https://tricore-emotion.vercel.app
- API — https://tricore-emotion-api.onrender.com ([interactive docs](https://tricore-emotion-api.onrender.com/docs))

The API is on Render's free tier, so the first request after 15 idle minutes
takes ~30-60 seconds while the service wakes up.

Three parts, each in its own folder:

| Folder      | What it is | Runs on |
|-------------|------------|---------|
| `training/` | A Python script that trains the model and saves it to disk | Your laptop, once |
| `backend/`  | A FastAPI server that loads the model and answers predictions | Render (or Hugging Face Spaces) |
| `frontend/` | A one-page Next.js app that talks to the backend | Vercel |

The model is TF-IDF + logistic regression from scikit-learn, trained on the
[`dair-ai/emotion`](https://huggingface.co/datasets/dair-ai/emotion) dataset.
It trains in a few seconds on a normal CPU and scores **87.5% accuracy on the
test split** — no GPU, no deep learning, nothing that needs a paid host.

---

## Quick start

Run these three sections in order the first time. The backend can't start until
training has produced a model.

### 1. Training (`training/`)

```bash
cd training
pip install -r requirements.txt
python train.py
```

This downloads the dataset (~2 MB), trains the model, prints a per-emotion
accuracy report, and writes three files into `training/model/`:

- `model.joblib` — the trained classifier
- `vectorizer.joblib` — the fitted TF-IDF vectorizer
- `labels.json` — the six label names in index order

Then copy those three files into the backend:

```bash
# macOS / Linux
cp -r model/* ../backend/model/

# Windows PowerShell
Copy-Item model\* ..\backend\model\ -Force
```

Expect a test accuracy in the high 80s. Rerunning `train.py` overwrites the
three files, so it's safe to run as often as you like.

### 2. Backend (`backend/`)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/docs** and try `/predict` right in the browser —
you can check the whole API works before touching the frontend.

Two endpoints:

- `GET /health` → `{"status": "ok"}`
- `POST /predict` with `{"text": "..."}` →

  ```json
  {
    "emotion": "joy",
    "confidence": 0.91,
    "emoji": "😄",
    "all_scores": { "sadness": 0.02, "joy": 0.91, "love": 0.03,
                    "anger": 0.01, "fear": 0.01, "surprise": 0.02 }
  }
  ```

Sending empty or whitespace-only text returns a `400` with
`"text must not be empty"`.

One environment variable:

| Variable       | Default                 | What it does |
|----------------|-------------------------|--------------|
| `FRONTEND_URL` | `http://localhost:3000` | The single origin CORS allows. Set it to your Vercel URL in production. |

### 3. Frontend (`frontend/`)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**. Make sure the backend is running first, or
every request will show the "couldn't reach the server" message.

`frontend/.env.local` (not committed) holds the backend address:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The page is one screen: a textarea, a few clickable example sentences, and a
result card with the emoji, the emotion, a confidence percentage, and a bar per
emotion so you can see how close the runner-up was.

> Note: this scaffold uses Tailwind v4, which is configured in
> `app/globals.css` via `@import "tailwindcss"` — there's no
> `tailwind.config.ts` to edit.

---

## Deploying

### Backend on Render (primary path)

1. Push this repo to GitHub, with `backend/model/` **included** — Render needs
   the trained files, and they're small enough (~850 KB total) to commit.
2. On [render.com](https://render.com): **New → Web Service**, connect the repo.
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Add environment variable `FRONTEND_URL` — set it to your Vercel URL once you
   have one (step below), then redeploy so CORS lets the frontend through.
4. Note the live URL, e.g. `https://your-app.onrender.com`.

No credit card needed for the free tier. **The free service sleeps after 15
minutes with no traffic and takes ~30-60 seconds to wake up.** That's expected,
not a bug — the frontend shows a "waking up the server…" message for exactly
this reason.

### Backend on Hugging Face Spaces (alternative)

Only if you'd rather keep everything on Hugging Face. Create a **Docker** Space
and push `backend/` — the included `Dockerfile` listens on port `7860`, which is
what Spaces expects. Check the current free-tier terms on
[huggingface.co/pricing](https://huggingface.co/pricing) first; the free CPU
tier policy has changed more than once.

### Frontend on Vercel

1. On [vercel.com](https://vercel.com), import the repo.
2. Set the root directory to `frontend` (this is a monorepo).
3. Add environment variable `NEXT_PUBLIC_API_URL` = your backend URL from above.
4. Deploy, then go back and set the backend's `FRONTEND_URL` to the
   `.vercel.app` URL Vercel gives you and redeploy the backend.

### End-to-end checklist

- [ ] `GET {backend_url}/health` returns `{"status": "ok"}`
- [ ] `POST {backend_url}/predict` returns a sensible emotion via `/docs` or curl
- [ ] The Vercel page loads and the example chips fill the textarea
- [ ] A prediction shows a matching emoji and bars adding up to ~100%
- [ ] Empty text shows a friendly error, not a crash
- [ ] The first request after idle shows the "waking up" message

---

## How good is it, really?

87.5% on the test split is an honest number, but it only describes sentences
that look like the training data — and `dair-ai/emotion` is tweets that nearly
all start with "i feel ...". So:

| Input | Prediction |
|-------|-----------|
| "i feel scared about the interview tomorrow" | fear, 93% ✅ |
| "i am amazed this actually happened" | surprise, 99% ✅ |
| "i am so angry about how they treated me" | anger, 67% ✅ |
| "This traffic is ridiculous" | joy, 26% ❌ |
| "I did not see that coming at all" | joy, 29% ❌ |

Terse sentences carry obvious emotion to a human but look nothing like the
training data, and the model guesses badly on them — usually with low confidence,
which the bar chart makes visible. This is a property of the dataset, not a bug
in the code. The example chips on the page use the phrasing the model actually
handles well.

Fixing it properly means training on more varied text, or fine-tuning a language
model that already understands English generally — the DistilBERT idea below.

## Ideas for later

- Swap in a fine-tuned DistilBERT model for a few extra accuracy points (needs a
  GPU to train — a free Colab session is enough — and a much bigger backend
  `requirements.txt`).
- Keep the last N predictions in React state as a history list.
- Dark mode with Tailwind's `dark:` classes.
- Batch mode: one prediction per line of a multi-line textarea.

## A note on the dataset

`dair-ai/emotion` is published for educational and research use. It's fine for a
portfolio or learning project; re-check the dataset license before using it in
anything commercial.
