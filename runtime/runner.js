// One Python worker per page, shared by every widget. Runs are queued so only
// one executes at a time; a run that exceeds its time limit terminates the
// worker and a fresh one is started for the next run.

const RUN_TIMEOUT_MS = 5_000;
const LOCAL_ASSETS = new URLSearchParams(location.search).has("localAssets");
const WORKER_URL = new URL(`./python-worker.js${LOCAL_ASSETS ? "?localAssets=1" : ""}`, import.meta.url);

export class TimeoutError extends Error {
  constructor(ms) {
    super(`Execution stopped after reaching the ${ms / 1000}-second time limit.`);
    this.name = "TimeoutError";
  }
}

export class StoppedError extends Error {
  constructor() {
    super("Execution stopped.");
    this.name = "StoppedError";
  }
}

class Runner {
  constructor() {
    this.worker = null;
    this.readyPromise = null;
    this.queue = Promise.resolve();
    this.listeners = new Set();
    this.state = "idle";
    this.current = null;
    this.nextId = 1;
  }

  /** Subscribe to status changes: fn(state, text). States: idle, loading, ready, running, error. */
  onStatus(fn) {
    this.listeners.add(fn);
    fn(this.state, this.statusText());
    return () => this.listeners.delete(fn);
  }

  statusText() {
    return { idle: "Python not loaded", loading: "Loading Python…", ready: "Python ready", running: "Running…", error: "Python failed to load" }[this.state];
  }

  setState(state) {
    this.state = state;
    for (const fn of this.listeners) fn(state, this.statusText());
  }

  /** Start loading Python now (e.g. on page load) instead of on the first run. */
  warmUp() {
    this.ensureWorker().catch(() => {});
  }

  ensureWorker() {
    if (this.readyPromise) return this.readyPromise;
    this.setState("loading");
    const worker = new Worker(WORKER_URL);
    this.worker = worker;
    this.readyPromise = new Promise((resolve, reject) => {
      const onMessage = (event) => {
        if (event.data?.type === "ready") {
          worker.removeEventListener("message", onMessage);
          this.setState("ready");
          resolve(worker);
        } else if (event.data?.type === "fatal") {
          worker.removeEventListener("message", onMessage);
          this.failWorker(new Error(event.data.error), reject);
        }
      };
      worker.addEventListener("message", onMessage);
      worker.addEventListener("error", () => this.failWorker(new Error("PyLab could not load the Python runtime. Check your connection and reload the page."), reject));
    });
    return this.readyPromise;
  }

  failWorker(error, reject) {
    this.worker?.terminate();
    this.worker = null;
    this.readyPromise = null;
    this.setState("error");
    reject(error);
  }

  /**
   * Run a project once. Resolves with the worker's result object
   * ({status, stdout, stderr, prompt, check}). Rejects with TimeoutError,
   * StoppedError, or a load error.
   */
  run({ files, entry = "main.py", inputs = [], echoInput = false, check = null, timeoutMs = RUN_TIMEOUT_MS }) {
    const job = () => this.execute({ files, entry, inputs, echoInput, check, timeoutMs });
    const result = this.queue.then(job, job);
    this.queue = result.catch(() => {});
    return result;
  }

  async execute(request) {
    const worker = await this.ensureWorker();
    this.setState("running");
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const finish = (fn, value) => {
        clearTimeout(timer);
        worker.removeEventListener("message", onMessage);
        if (this.current?.id === id) this.current = null;
        if (this.state === "running") this.setState("ready");
        fn(value);
      };
      const onMessage = (event) => {
        if (event.data?.type === "result" && event.data.id === id) finish(resolve, event.data);
      };
      const timer = setTimeout(() => {
        this.restart();
        finish(reject, new TimeoutError(request.timeoutMs));
      }, request.timeoutMs);
      this.current = { id, abort: () => { this.restart(); finish(reject, new StoppedError()); } };
      worker.addEventListener("message", onMessage);
      worker.postMessage({ type: "run", id, ...request });
    });
  }

  /** Abort the run in progress, if any. */
  stop() {
    this.current?.abort();
  }

  restart() {
    this.worker?.terminate();
    this.worker = null;
    this.readyPromise = null;
    this.setState("idle");
    this.warmUp();
  }
}

export const runner = new Runner();

/**
 * Run a program interactively against a console: output is appended as it
 * arrives, and each input() prompt becomes an inline text field. Resolves
 * with the final result once the program finishes (or errors).
 *
 * console must provide: append(text), prompt(text) -> Promise<string>,
 * error(text). Returns {status, stdout, stderr}.
 */
export async function runInteractive({ files, entry, console: out, inputs = [], signal }) {
  const answers = [...inputs];
  let shown = "";
  for (;;) {
    const result = await runner.run({ files, entry, inputs: answers, echoInput: true });
    // Replay is deterministic for course programs, so the new output is the
    // suffix past what is already on screen. If it isn't, redraw everything.
    if (result.stdout.startsWith(shown)) {
      out.append(result.stdout.slice(shown.length));
    } else {
      out.clear();
      out.append(result.stdout);
    }
    shown = result.stdout;
    if (result.status !== "need-input") {
      if (result.stderr) out.error(result.stderr);
      return result;
    }
    if (signal?.aborted) throw new StoppedError();
    const answer = await out.prompt(signal);
    answers.push(answer);
    shown += answer + "\n";
  }
}
