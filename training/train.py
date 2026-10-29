"""
Train an emotion classifier on the dair-ai/emotion dataset.

Run it once with:

    python train.py

It prints how well the model does and writes three files into training/model/:
model.joblib, vectorizer.joblib and labels.json. Those three files are
everything the backend needs to make predictions.
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

# Where the trained files go. Path(__file__).parent means "next to this script",
# so it works no matter which folder you run `python train.py` from.
MODEL_DIR = Path(__file__).parent / "model"


def load_data():
    """Download the dataset and return three DataFrames plus the label names.

    We use the "split" config because it already comes divided into train /
    validation / test. The "unsplit" config is one big pile of rows and we would
    have to split it ourselves.
    """
    dataset = load_dataset("dair-ai/emotion", "split")

    train_df = pd.DataFrame(dataset["train"])
    validation_df = pd.DataFrame(dataset["validation"])
    test_df = pd.DataFrame(dataset["test"])

    # Read the label names from the dataset itself instead of typing them out
    # by hand. If the dataset ever changes its label order, our labels.json
    # follows along automatically instead of silently going out of sync.
    label_names = dataset["train"].features["label"].names

    print(f"Loaded {len(train_df)} train / {len(validation_df)} validation / "
          f"{len(test_df)} test rows.")
    print(f"Labels (in index order): {label_names}")

    return train_df, validation_df, test_df, label_names


def build_pipeline():
    """Create the two objects that make up the model.

    Kept as two separate objects rather than a scikit-learn Pipeline because the
    backend saves and loads them separately, and because it makes the two steps
    obvious: turn text into numbers, then classify the numbers.
    """
    # max_features caps the vocabulary at the 10,000 most useful terms so the
    # saved model stays small. ngram_range=(1, 2) also looks at word pairs, which
    # is how the model can tell "not happy" apart from "happy".
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))

    # class_weight="balanced" matters here: love and surprise have far fewer
    # examples than joy and sadness. Without it the model can score well simply
    # by never predicting the rare emotions. "balanced" makes mistakes on rare
    # classes cost more, so the model actually has to learn them.
    model = LogisticRegression(max_iter=1000, class_weight="balanced")

    return vectorizer, model


def evaluate(model, vectorizer, df, split_name, label_names):
    """Print accuracy and a per-emotion report for one split."""
    features = vectorizer.transform(df["text"])
    predictions = model.predict(features)

    accuracy = accuracy_score(df["label"], predictions)
    print(f"\n--- {split_name} ---")
    print(f"Accuracy: {accuracy:.1%}")
    print(classification_report(
        df["label"],
        predictions,
        target_names=label_names,
        # The dataset uses integer labels 0-5, so spell out which integers map to
        # which name. Without this, a split missing a rare class would misalign
        # the report's rows.
        labels=list(range(len(label_names))),
        zero_division=0,
    ))

    return accuracy


def train_and_evaluate(train_df, validation_df, test_df, label_names):
    """Fit the model on the training split, then score it on the other two."""
    vectorizer, model = build_pipeline()

    print("\nTraining...")
    # fit_transform learns the vocabulary AND converts the text. Every later
    # split uses plain transform() so it reuses that same vocabulary — fitting
    # the vectorizer on validation or test data would leak information.
    train_features = vectorizer.fit_transform(train_df["text"])
    model.fit(train_features, train_df["label"])
    print("Done.")

    # Validation is the number you look at while tweaking settings.
    evaluate(model, vectorizer, validation_df, "VALIDATION", label_names)

    # Test is the honest final number. Look at it once, at the end, and resist
    # tuning against it — otherwise it stops being an honest number.
    test_accuracy = evaluate(model, vectorizer, test_df, "TEST", label_names)

    print(f"\nTest accuracy: {test_accuracy:.1%}")

    return model, vectorizer


def save_artifacts(model, vectorizer, label_names):
    """Write the three files the backend loads at startup."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODEL_DIR / "model.joblib")
    joblib.dump(vectorizer, MODEL_DIR / "vectorizer.joblib")

    # A plain JSON list, in index order, so index 0 of the model's output maps to
    # label_names[0]. JSON rather than joblib because a human can open it.
    with open(MODEL_DIR / "labels.json", "w", encoding="utf-8") as f:
        json.dump(label_names, f, indent=2)

    print(f"\nSaved model.joblib, vectorizer.joblib and labels.json to {MODEL_DIR}")
    print("Copy those three files into backend/model/ before running the API.")


if __name__ == "__main__":
    train_df, validation_df, test_df, label_names = load_data()
    model, vectorizer = train_and_evaluate(
        train_df, validation_df, test_df, label_names
    )
    save_artifacts(model, vectorizer, label_names)
