"use client";

import { useState } from "react";
import EmotionForm from "@/components/EmotionForm";
import ExampleChips from "@/components/ExampleChips";
import ResultCard, { type Prediction } from "@/components/ResultCard";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function Home() {
  const [text, setText] = useState("");
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function analyze() {
    setLoading(true);
    setError("");
    // Clear the old result so a stale prediction isn't left on screen next to
    // a new sentence while the request is running.
    setPrediction(null);

    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) {
        // The backend sends 400 with a readable message for things like empty
        // text, so show that rather than a generic failure.
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? "The server rejected that request.");
      }

      setPrediction(await res.json());
    } catch {
      setError(
        "Couldn't reach the server — it might still be waking up, try again in a few seconds."
      );
    } finally {
      // In a finally block so the button is re-enabled whether the request
      // succeeded or failed.
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-3xl font-bold">Emotion Classifier</h1>
      <p className="mt-2 text-slate-600">
        Type how you&apos;re feeling and see what emotion it maps to.
      </p>

      <div className="mt-8">
        <EmotionForm
          text={text}
          onTextChange={setText}
          onSubmit={analyze}
          loading={loading}
        />
        <ExampleChips onPick={setText} />
      </div>

      {error && (
        <p className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
          {error}
        </p>
      )}

      {prediction && <ResultCard prediction={prediction} />}
    </main>
  );
}
