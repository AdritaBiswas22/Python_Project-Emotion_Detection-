"""
FastAPI server for the emotion classifier.

Run it locally with:

    uvicorn main:app --reload --port 8000

Then open http://localhost:8000/docs to try the /predict endpoint straight from
the browser, no frontend needed.
"""

import json
import os
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

MODEL_DIR = Path(__file__).parent / "model"

# One emoji per emotion, shown next to the result on the frontend. A plain dict
# is all this needs.
EMOJI = {
    "sadness": "😢",
    "joy": "😄",
    "love": "❤️",
    "anger": "😠",
    "fear": "😨",
    "surprise": "😲",
}

# Load the model once, when the server starts. Loading it inside the /predict
# handler instead would re-read the files from disk on every single request,
# which would make each prediction hundreds of times slower.
model = joblib.load(MODEL_DIR / "model.joblib")
vectorizer = joblib.load(MODEL_DIR / "vectorizer.joblib")
with open(MODEL_DIR / "labels.json", encoding="utf-8") as f:
    LABELS = json.load(f)

app = FastAPI(
    title="Emotion Classifier API",
    description="Predicts one of six emotions from a sentence.",
)

# The browser blocks requests from the frontend unless the backend says that
# origin is allowed. The URL comes from an environment variable so the
# production Vercel address is configured at deploy time, not baked into the
# code. Set FRONTEND_URL on Render once the frontend is live.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    emotion: str
    confidence: float
    emoji: str
    all_scores: dict[str, float]


@app.get("/health")
def health():
    """A cheap endpoint to check the server is up (and to wake it from sleep)."""
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """Predict the emotion behind a single sentence."""
    text = request.text.strip()
    if not text:
        # Catch this here rather than letting the model try to classify an empty
        # string, which would return a meaningless but confident-looking answer.
        raise HTTPException(status_code=400, detail="text must not be empty")

    # The vectorizer expects a list of documents, so pass a one-item list and
    # read back the one row of results.
    features = vectorizer.transform([text])

    # predict_proba gives a score for every emotion, not just the winner. That's
    # what fills in all_scores and the confidence bars on the frontend.
    probabilities = model.predict_proba(features)[0]

    # model.classes_ holds the label indexes in the same order as the columns of
    # probabilities. Pairing them explicitly avoids assuming the order is 0..5.
    all_scores = {
        LABELS[class_index]: round(float(probability), 4)
        for class_index, probability in zip(model.classes_, probabilities)
    }

    top_emotion = max(all_scores, key=all_scores.get)

    return PredictResponse(
        emotion=top_emotion,
        confidence=all_scores[top_emotion],
        emoji=EMOJI.get(top_emotion, "🙂"),
        all_scores=all_scores,
    )
