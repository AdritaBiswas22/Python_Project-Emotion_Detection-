// The shape of what /predict sends back. page.tsx imports this too, so the
// frontend and the backend agree on one description of a prediction.
export type Prediction = {
  emotion: string;
  confidence: number;
  emoji: string;
  all_scores: Record<string, number>;
};

// One accent colour per emotion, used for that emotion's bar. Written out as
// full Tailwind class names on purpose — Tailwind scans the source for complete
// class strings, so something like `bg-${color}-500` would be stripped from the
// final CSS and the bars would come out invisible.
const BAR_COLOR: Record<string, string> = {
  sadness: "bg-blue-500",
  joy: "bg-yellow-500",
  love: "bg-pink-500",
  anger: "bg-red-500",
  fear: "bg-purple-500",
  surprise: "bg-orange-500",
};

function toPercent(score: number) {
  return Math.round(score * 100);
}

export default function ResultCard({ prediction }: { prediction: Prediction }) {
  // Show the strongest emotion first so the bars read as a ranking.
  const sortedScores = Object.entries(prediction.all_scores).sort(
    (a, b) => b[1] - a[1]
  );

  return (
    <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-4">
        <span className="text-6xl">{prediction.emoji}</span>
        <div>
          <p className="text-3xl font-semibold capitalize">
            {prediction.emotion}
          </p>
          <p className="text-slate-500">
            {toPercent(prediction.confidence)}% confident
          </p>
        </div>
      </div>

      <div className="mt-6 space-y-2">
        {sortedScores.map(([emotion, score]) => (
          <div key={emotion} className="flex items-center gap-3">
            <span className="w-20 shrink-0 text-sm capitalize text-slate-600">
              {emotion}
            </span>
            <div className="h-3 flex-1 overflow-hidden rounded-full bg-slate-100">
              {/* An inline width is the simplest way to size the bar, since the
                  percentage is only known at runtime. */}
              <div
                className={`h-full rounded-full ${
                  BAR_COLOR[emotion] ?? "bg-slate-400"
                }`}
                style={{ width: `${toPercent(score)}%` }}
              />
            </div>
            <span className="w-10 shrink-0 text-right text-sm tabular-nums text-slate-500">
              {toPercent(score)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
