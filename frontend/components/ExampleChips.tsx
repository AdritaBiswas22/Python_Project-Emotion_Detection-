// A few ready-made sentences so a first-time visitor can try the app without
// having to think of something to type. One per emotion, so clicking through
// them shows off all six classes.
//
// They're all phrased as "I feel / I am ..." on purpose. The training data is
// tweets that almost all start that way, so that's the phrasing the model is
// genuinely good at. Terse sentences like "This traffic is ridiculous" carry
// obvious emotion to a human but are unlike anything the model saw in training,
// and it guesses badly on them. See the README for more on this limitation.
const EXAMPLES = [
  "I feel so happy about the news",
  "I am feeling really down today",
  "I feel loved and supported by my family",
  "I am so angry about how they treated me",
  "I feel scared about the interview tomorrow",
  "I am amazed this actually happened",
];

export default function ExampleChips({
  onPick,
}: {
  onPick: (example: string) => void;
}) {
  return (
    <div className="mt-4">
      <p className="mb-2 text-sm text-slate-500">Or try an example:</p>
      <div className="flex flex-wrap gap-2">
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => onPick(example)}
            className="rounded-full border border-slate-300 bg-white px-3 py-1 text-sm text-slate-700 hover:border-slate-400 hover:bg-slate-50"
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}
