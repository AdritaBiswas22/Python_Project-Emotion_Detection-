# Project Brief: Emotion Classifier (for Claude Code)

> **How to use this file:** Save this as `prompt.md` in an empty project folder,
> then start Claude Code in that folder (`claude`) and say:
> `"Read prompt.md and build Phase 1. Stop and show me the result before moving on."`
> Work through the phases in order — don't let it do everything in one shot.
> After each phase, run the app and check it actually works before continuing.

## 0. What we're building

A simple web app that reads a sentence and predicts the emotion behind it —
one of six classes: **sadness, joy, love, anger, fear, surprise**.

Three pieces:
1. **Training** — a Python script that trains a small, fast text-classification
   model on the `dair-ai/emotion` dataset and saves it to disk.
2. **Backend** — a FastAPI server that loads the trained model and exposes a
   `/predict` endpoint. Deployed on **Render** (primary) or **Hugging Face
   Spaces** (alternative).
3. **Frontend** — a clean, simple Next.js page: type a sentence, click a
   button, see the predicted emotion with an emoji and a confidence bar.
   Deployed on **Vercel**.

**Guiding rule for all code: optimize for a beginner reading it for the first
time.** Short functions, obvious names, comments that explain *why* not just
*what*, no clever one-liners, no unnecessary abstraction layers or design
patterns. If there's a choice between "elegant" and "obvious", pick obvious.

---

## 1. The dataset

Hugging Face dataset: [`dair-ai/emotion`](https://huggingface.co/datasets/dair-ai/emotion)

- Use the **`split`** config (not `unsplit`) — it comes pre-divided into:
  - `train`: 16,000 rows
  - `validation`: 2,000 rows
  - `test`: 2,000 rows
- Each row: `{"text": "im feeling quite sad and sorry for myself...", "label": 0}`
- Labels (already integer-encoded by the dataset, in this order):
  `0=sadness, 1=joy, 2=love, 3=anger, 4=fear, 5=surprise`
- Text is English tweets, already lowercased with punctuation stripped —
  minimal cleaning needed.
- **Classes are imbalanced** (joy and sadness are the largest classes; love
  and surprise are much smaller). Handle this with `class_weight="balanced"`
  in the model — don't just ignore it.
- License: for educational/research use — fine for a portfolio/learning
  project; don't productize it commercially without checking the dataset
  license again.

---

## 2. Tech stack (and why)

| Layer     | Choice                              | Why |
|-----------|--------------------------------------|-----|
| Training  | Python + scikit-learn (TF-IDF + Logistic Regression) | Trains in seconds on a laptop CPU, no GPU needed, and the whole pipeline is ~40 lines of code a beginner can read top to bottom. Good enough accuracy (~88-89%) on this dataset. |
| Backend   | FastAPI + Uvicorn                    | Minimal boilerplate, automatic request validation, built-in interactive docs at `/docs` which is great for a beginner to test the API without a frontend. |
| Backend hosting | Render (free web service)     | No credit card required to start, deploys straight from GitHub, one build command + one start command. Free tier sleeps after 15 minutes of no traffic and takes ~30-60s to wake back up on the next request — that's expected, not a bug. |
| Backend hosting (alt) | Hugging Face Spaces (Docker SDK) | Also works well for a Python API, keeps model + backend on the same platform as the dataset. **Check the current free-tier terms on huggingface.co/pricing before committing** — Spaces' free CPU tier policy has changed more than once recently, so confirm it's still available and suitable before building around it. |
| Frontend  | Next.js (App Router) + Tailwind CSS  | One command to scaffold (`create-next-app`), Vercel deploys it with zero config, Tailwind keeps styling readable inline instead of juggling separate CSS files. |
| Frontend hosting | Vercel                        | Built by the makers of Next.js, free tier is plenty for a personal project, connects directly to a GitHub repo for auto-deploys. |

Do **not** reach for a deep learning model (BERT/DistilBERT fine-tuning) for
the main build — it adds GPU considerations, longer training time, and a much
bigger `requirements.txt` that's harder to deploy on free hosting. It's listed
as an optional stretch goal in Section 8 once the simple version is working.

---

## 3. Repository structure

```
emotion-classifier/
├── training/
│   ├── train.py              # loads data, trains model, saves artifacts
│   ├── requirements.txt
│   └── model/                # OUTPUT of training — copy this into backend/model/
│       ├── model.joblib
│       ├── vectorizer.joblib
│       └── labels.json
│
├── backend/
│   ├── main.py                # FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile             # only needed for Hugging Face Spaces deploy
│   └── model/                 # copy trained artifacts here before deploying
│       ├── model.joblib
│       ├── vectorizer.joblib
│       └── labels.json
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # the single page of the app
│   │   └── layout.tsx
│   ├── components/
│   │   ├── EmotionForm.tsx    # textarea + submit button
│   │   ├── ResultCard.tsx     # emoji + label + confidence bar chart
│   │   └── ExampleChips.tsx   # a few clickable example sentences
│   ├── .env.local             # NEXT_PUBLIC_API_URL=http://localhost:8000
│   ├── package.json
│   └── tailwind.config.ts
│
└── README.md                  # setup + run instructions for all three parts
```

---

## 4. Phase 1 — Training pipeline (`training/train.py`)

**Goal:** a script you run once (`python train.py`) that prints accuracy and
saves three files into `training/model/`.

Steps the script should perform, in order, each as a clearly named function:

1. `load_data()` — use the `datasets` library:
   ```python
   from datasets import load_dataset
   dataset = load_dataset("dair-ai/emotion", "split")
   ```
   Pull `dataset["train"]`, `dataset["validation"]`, `dataset["test"]` and
   convert each to a pandas DataFrame with `text` and `label` columns. Also
   grab the human-readable label names from
   `dataset["train"].features["label"].names` — don't hardcode the label
   list by hand, read it from the dataset so it can never drift out of sync.

2. `build_pipeline()` — a scikit-learn `Pipeline` (or just two separate
   objects, whichever is easier to explain in comments) combining:
   - `TfidfVectorizer(max_features=10000, ngram_range=(1, 2))`
   - `LogisticRegression(max_iter=1000, class_weight="balanced")`

3. `train_and_evaluate()` — fit on the train split, then:
   - print accuracy and a full `classification_report` on the **validation**
     split (this is what you look at while iterating)
   - print accuracy and a full `classification_report` on the **test** split
     (this is the final, "don't touch it again" number)
   - print a short plain-English summary, e.g. `"Test accuracy: 88.4%"`

4. `save_artifacts()` — using `joblib.dump()`, save into `training/model/`:
   - `model.joblib` — the trained classifier
   - `vectorizer.joblib` — the fitted TF-IDF vectorizer
   - `labels.json` — a JSON list of label names in index order, e.g.
     `["sadness", "joy", "love", "anger", "fear", "surprise"]`

5. A `if __name__ == "__main__":` block that calls all of the above in order.

`training/requirements.txt`:
```
datasets
scikit-learn
pandas
joblib
```

**Acceptance check for this phase:** running `python train.py` finishes in
under a minute on a normal laptop, prints a test accuracy in the
mid-to-high 80s%, and leaves exactly three files in `training/model/`.

---

## 5. Phase 2 — Backend (`backend/main.py`)

**Goal:** a FastAPI app that loads the three saved artifacts once at startup
and answers predictions over HTTP.

### API contract

`GET /health`
```json
{"status": "ok"}
```

`POST /predict`

Request body:
```json
{"text": "I can't believe how happy I feel right now"}
```

Response body:
```json
{
  "emotion": "joy",
  "confidence": 0.91,
  "emoji": "😄",
  "all_scores": {
    "sadness": 0.02,
    "joy": 0.91,
    "love": 0.03,
    "anger": 0.01,
    "fear": 0.01,
    "surprise": 0.02
  }
}
```

### Implementation notes

- Use `pydantic.BaseModel` for the request (`class PredictRequest: text: str`)
  and response models — this gives free input validation and shows up nicely
  in the auto-generated docs at `/docs`.
- Load `model.joblib`, `vectorizer.joblib`, and `labels.json` **once**,
  at module level or in a startup event — never reload them per-request.
- If `text` is empty or only whitespace, return a `400` error with a clear
  message (`"text must not be empty"`) instead of trying to predict.
- Use `model.predict_proba()` to get a probability for every class, not just
  `model.predict()` — that's what powers `all_scores` and the confidence bar
  chart on the frontend.
- Emoji mapping (keep it as a plain dict, no need for anything fancier):
  ```python
  EMOJI = {
      "sadness": "😢", "joy": "😄", "love": "❤️",
      "anger": "😠", "fear": "😨", "surprise": "😲",
  }
  ```
- **CORS:** add `fastapi.middleware.cors.CORSMiddleware`, allowing the
  frontend's origin. Read the allowed origin from an environment variable
  (`FRONTEND_URL`) with `http://localhost:3000` as the local default, so you
  don't hardcode the production Vercel URL into the code.

`backend/requirements.txt`:
```
fastapi
uvicorn[standard]
scikit-learn
joblib
pydantic
```

### Local test

```
uvicorn main:app --reload --port 8000
```
Then open `http://localhost:8000/docs` and try `/predict` right from the
browser before touching the frontend at all.

### Deploying to Render (primary path)

1. Push the `backend/` folder to a GitHub repo (with `model/` included, or
   see the note below).
2. On [render.com](https://render.com), create a **New Web Service**, connect
   the repo, and set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add environment variable `FRONTEND_URL` = your Vercel URL once you have
     it (Section 7).
3. No credit card is required for Render's free tier. The service will sleep
   after 15 minutes of no requests and take roughly 30-60 seconds to wake up
   on the next call — mention this on the frontend (a "waking up the
   server…" loading message) so it doesn't look broken.
4. Note the live URL, something like `https://your-app.onrender.com` — you'll
   need it for the frontend's `NEXT_PUBLIC_API_URL`.

### Deploying to Hugging Face Spaces (alternative path)

Only do this instead of Render if you'd rather keep everything on Hugging
Face. Create a **Docker** Space and add this `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

Hugging Face Docker Spaces expect the app to listen on port `7860` — that's
the one thing that's different from the Render setup above. Verify current
free-tier availability and any SDK restrictions on huggingface.co/pricing
before relying on this path, since it's changed recently.

---

## 6. Phase 3 — Frontend (`frontend/`)

**Goal:** one clean page. Not a dashboard, not a multi-page app — a single
screen that feels approachable.

### Scaffold

```
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
```

### Page layout (`app/page.tsx`)

1. A short title and one-sentence description at the top
   ("Type how you're feeling and see what emotion it maps to.").
2. `<EmotionForm />` — a textarea and a submit button labeled
   "Analyze Emotion". Disable the button while a request is in flight, and
   show a small loading message under it (mention the possible ~30-60s
   Render cold start the first time).
3. A few clickable example sentences via `<ExampleChips />` (e.g. "I got the
   job!", "I miss my old dog", "This traffic is ridiculous") that fill the
   textarea when clicked — this makes the app instantly usable for a first-
   time visitor with nothing to type.
4. `<ResultCard />` — after a prediction comes back, show:
   - a big emoji for the top emotion
   - the emotion name in a large, friendly font
   - a confidence percentage
   - a simple horizontal bar per emotion (using `all_scores`) so the user can
     see it wasn't a coin flip — plain divs with a `width: {percent}%` style
     is enough, no charting library required.
5. A clear error state if the fetch fails (e.g. "Couldn't reach the server —
   it might still be waking up, try again in a few seconds.").

### Fetching the API

```ts
const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/predict`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text }),
});
```

`.env.local` (not committed to git):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Styling guidance

- Tailwind utility classes directly in JSX — no separate CSS files to jump
  between.
- One accent color per emotion is a nice beginner-friendly touch (e.g. blue
  for sadness, yellow for joy, pink for love, red for anger, purple for fear,
  orange for surprise) — a plain object mapping emotion → Tailwind color
  class is enough, no need for a design system.
- Keep the whole page usable on a phone screen — it's one column already, so
  this should fall out naturally if you avoid fixed pixel widths.

### Deploying to Vercel

1. Push `frontend/` to GitHub.
2. On [vercel.com](https://vercel.com), import the repo, set the root
   directory to `frontend` if it's part of a monorepo.
3. Add the environment variable `NEXT_PUBLIC_API_URL` = your Render (or HF
   Spaces) backend URL from Section 5.
4. Deploy. Vercel gives you a live `.vercel.app` URL.
5. Go back to the backend's `FRONTEND_URL` environment variable and set it to
   this Vercel URL, then redeploy the backend so CORS allows it.

---

## 7. Phase 4 — Connect and verify end to end

Checklist to run through once both are deployed:

- [ ] `GET {backend_url}/health` returns `{"status": "ok"}`
- [ ] `POST {backend_url}/predict` with a sample sentence returns a sensible
      emotion via `curl` or the `/docs` page
- [ ] The Vercel frontend loads and the example chips fill the textarea
- [ ] Submitting text shows a result with a matching emoji and a confidence
      bar chart that sums to roughly 100%
- [ ] Submitting empty text shows a friendly error, not a crash
- [ ] The first request after a period of inactivity shows the "waking up"
      message instead of just hanging silently

---

## 8. Stretch goals (only after the above works end to end)

Pick these up one at a time, and keep the simple version working as a
fallback while you experiment:

- **Swap in a fine-tuned DistilBERT model** using Hugging Face
  `transformers` (`Trainer` API) for a few extra points of accuracy. This
  needs more compute to train (a free Google Colab GPU is enough) and a
  bigger `requirements.txt` on the backend — budget more deploy time for it.
- **Prediction history** — store the last N predictions in the browser
  (React state is enough; no backend database needed for a personal
  project).
- **Dark mode** toggle using Tailwind's `dark:` classes.
- **Batch mode** — a textarea that accepts multiple lines and returns one
  prediction per line.

---

## 9. Code style reminders for Claude Code while building this

- Prefer plain functions over classes unless state genuinely needs to be
  bundled together.
- Comment the *why*, not the obvious *what* (skip `# increment i` next to
  `i += 1`; do explain *why* `class_weight="balanced"` is used).
- No premature abstraction — don't build a plugin system or config framework
  for a 3-file backend.
- Every folder (`training/`, `backend/`, `frontend/`) gets a short section in
  the root `README.md` with the exact commands to install and run it locally.
- Stop after each phase and let the human run the code before continuing —
  don't chain all four phases into one uninterrupted pass.
