// Instructor mode: a hidden switch for checking questions and answers
// without the student-facing limits. While it is on, locked workbooks open
// and model answers show without spending XP or asking first.
//
// Turn it on or off by opening any page with ?pranjal_mode=on or
// ?pranjal_mode=off. The setting is kept in localStorage for this browser
// only.

const KEY = "pylab-workbooks:instructor";
const PARAM = "pranjal_mode";

export function isInstructor() {
  try { return localStorage.getItem(KEY) === "1"; } catch { return false; }
}

export function setInstructor(on) {
  try {
    if (on) localStorage.setItem(KEY, "1");
    else localStorage.removeItem(KEY);
  } catch { /* ignore */ }
}

/** Apply the URL switch, then drop it from the address bar. */
export function initInstructor() {
  const param = new URLSearchParams(location.search).get(PARAM);
  if (param !== "on" && param !== "off") return;
  setInstructor(param === "on");
  const url = new URL(location.href);
  url.searchParams.delete(PARAM);
  history.replaceState(null, "", url);
}

/** A small badge for the top bar; hidden unless instructor mode is on. Click to turn it off. */
export function instructorBadge() {
  const badge = document.createElement("button");
  badge.type = "button";
  badge.className = "wb-instructor-badge";
  badge.textContent = "Instructor";
  badge.title = "Instructor mode is on: locks and XP prices are off. Click to turn it off.";
  badge.hidden = !isInstructor();
  badge.addEventListener("click", () => {
    if (!window.confirm("Turn instructor mode off?")) return;
    setInstructor(false);
    location.reload();
  });
  return badge;
}
