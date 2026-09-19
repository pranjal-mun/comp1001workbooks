// Pages start hidden (see `body:not(.wb-ready)` in workbook.css) so the top
// bar, contents, widgets, and web fonts are all in place before the first
// paint instead of jumping into position. Call revealPage() once the page
// has built its chrome. The CSS shows the page on its own after two seconds
// in case a script fails.

export async function revealPage() {
  const fonts = document.fonts?.ready ?? Promise.resolve();
  await Promise.race([fonts, new Promise((r) => setTimeout(r, 1000))]);
  document.body.classList.add("wb-ready");
}
