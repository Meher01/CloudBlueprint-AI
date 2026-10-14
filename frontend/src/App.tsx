import { useState } from "react";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

type PlanResponse = {
  plan: string;
  model: string;
};

const SECTION_HEADING = /^\*\*(\d+\.\s+(?:Project summary|Suggested features|AWS architecture|Data flow|Security and privacy considerations|Build phases))\*\*$/;

function App() {
  const [title, setTitle] = useState("");
  const [problem, setProblem] = useState("");
  const [projectType, setProjectType] = useState("");
  const [features, setFeatures] = useState("");
  const [result, setResult] = useState<PlanResponse | null>(null);
  const [error, setError] = useState("");
  const [completionNotice, setCompletionNotice] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    setCompletionNotice(false);

    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, problem, projectType, features }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail ?? "The plan could not be generated.");
      }

      setResult((await response.json()) as PlanResponse);
      setCompletionNotice(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not connect to the backend.",
      );
    } finally {
      setLoading(false);
    }
  }

  function downloadPlan() {
    if (!result) return;

    const plainTextPlan = result.plan.replace(/^\*\*(.+)\*\*$/gm, "$1");
    const file = new Blob([plainTextPlan], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(file);
    const link = document.createElement("a");

    link.href = url;
    link.download = `${title.trim().replace(/[^a-z0-9]+/gi, "-").toLowerCase() || "aws-project-plan"}.txt`;
    link.click();

    URL.revokeObjectURL(url);
  }

  return (
    <main>
      {completionNotice && (
        <div className="completion-notice" role="status">
          <span aria-hidden="true">✓</span>
          <span>Generation is complete, Scroll further!</span>
          <button
            type="button"
            className="completion-notice-dismiss"
            onClick={() => setCompletionNotice(false)}
            aria-label="Dismiss completion message"
          >
            ×
          </button>
        </div>
      )}
      <h1>AWS CloudBlueprint AI</h1>
      <hr></hr>
      <h2>Turn your project idea into an AWS architecture plan.</h2>

      <form onSubmit={handleSubmit}>
        <label htmlFor="title">Project title</label>
        <input
          id="title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
        />

        <label htmlFor="problem">Problem to solve</label>
        <textarea
          id="problem"
          value={problem}
          onChange={(event) => setProblem(event.target.value)}
          required
        />

        <label htmlFor="projectType">Who will use it, and where?</label>
        <textarea
          id="projectType"
          value={projectType}
          onChange={(event) => setProjectType(event.target.value)}
          placeholder="For example: a public website for local event organizers"
        />

        <label htmlFor="features">Features you have in mind</label>
        <textarea
          id="features"
          value={features}
          onChange={(event) => setFeatures(event.target.value)}
          placeholder="One feature per line. . ."
        />

        <button type="submit" disabled={loading}>
          {loading ? "Generating plan..." : "Generate plan"}
        </button>
        <button type="button" onClick={downloadPlan}>
          Download plan
        </button>

        {loading && (
          <p role="status">
            Qwen is checking your idea and drafting a plan. This can take a little while on a local machine.
          </p>
        )}
      </form>
      
      {error && <p role="alert">{error}</p>}

      {result && (
        <section>
          <h2>Your AWS project plan</h2>
          <p>Generated with {result.model}</p>
          <div className="plan-output">
            {result.plan.split("\n").map((line, index) => {
              const heading = SECTION_HEADING.exec(line);
              return (
                <div
                  className={heading ? "plan-heading" : line.trim() ? "plan-line" : "plan-spacer"}
                  key={`${index}-${line}`}
                >
                  {heading ? <strong>{heading[1]}</strong> : line || "\u00a0"}
                </div>
              );
            })}
          </div>
        </section>
      )}
    </main>
  );
}

export default App;