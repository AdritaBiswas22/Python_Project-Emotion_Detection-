export default function EmotionForm({
  text,
  onTextChange,
  onSubmit,
  loading,
}: {
  text: string;
  onTextChange: (text: string) => void;
  onSubmit: () => void;
  loading: boolean;
}) {
  return (
    <form
      onSubmit={(event) => {
        // Without this the browser reloads the page on submit and the result
        // disappears the moment it arrives.
        event.preventDefault();
        onSubmit();
      }}
    >
      <textarea
        value={text}
        onChange={(event) => onTextChange(event.target.value)}
        rows={4}
        placeholder="Type how you're feeling..."
        className="w-full resize-none rounded-xl border border-slate-300 bg-white p-4 outline-none focus:border-slate-500"
      />

      <button
        type="submit"
        // Blocked while a request is in flight so an impatient double-click
        // doesn't fire two predictions at once.
        disabled={loading || text.trim() === ""}
        className="mt-3 w-full rounded-xl bg-slate-900 px-4 py-3 font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {loading ? "Analyzing..." : "Analyze Emotion"}
      </button>

      {loading && (
        // The free Render tier sleeps after 15 minutes idle, so the first
        // request of the day really can take this long. Saying so up front
        // stops it from looking broken.
        <p className="mt-2 text-center text-sm text-slate-500">
          Waking up the server... the first request can take 30-60 seconds.
        </p>
      )}
    </form>
  );
}
