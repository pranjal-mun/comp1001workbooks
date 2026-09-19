// A program console: printed output, error text, and inline input() prompts,
// the way IDLE shows them. Used by every runnable widget and by the lab.

export class Console {
  constructor(element) {
    this.element = element;
    this.element.classList.add("wb-console");
    this.element.setAttribute("aria-live", "polite");
    this.clear();
  }

  clear() {
    this.element.replaceChildren();
    this.pendingInput = null;
    this.element.classList.remove("has-error");
  }

  append(text, className = "wb-console-out") {
    if (!text) return;
    const span = document.createElement("span");
    span.className = className;
    span.textContent = text;
    this.element.append(span);
    this.element.scrollTop = this.element.scrollHeight;
  }

  error(text) {
    this.element.classList.add("has-error");
    this.append(text, "wb-console-err");
  }

  note(text) {
    this.append(text, "wb-console-note");
  }

  get isEmpty() {
    return this.element.childNodes.length === 0;
  }

  /** Show an inline text field at the end of the output; resolves with the typed line. */
  prompt(signal) {
    const field = document.createElement("input");
    field.type = "text";
    field.className = "wb-console-input";
    field.setAttribute("aria-label", "Program input");
    field.autocomplete = "off";
    field.spellcheck = false;
    this.element.append(field);
    this.element.scrollTop = this.element.scrollHeight;
    field.focus();
    return new Promise((resolve, reject) => {
      const done = (answer) => {
        cleanup();
        field.remove();
        this.append(answer + "\n", "wb-console-typed");
        resolve(answer);
      };
      const onKey = (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          done(field.value);
        }
      };
      const onAbort = () => {
        cleanup();
        field.remove();
        reject(new DOMException("Aborted", "AbortError"));
      };
      const cleanup = () => {
        field.removeEventListener("keydown", onKey);
        signal?.removeEventListener("abort", onAbort);
        this.pendingInput = null;
      };
      field.addEventListener("keydown", onKey);
      signal?.addEventListener("abort", onAbort);
      this.pendingInput = { cancel: onAbort };
    });
  }
}
