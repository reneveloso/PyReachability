# Verbatim paper examples (fidelity suite)

*Guia em português: [README_pt.md](README_pt.md).*

Each `<method>.py` file in this folder transcribes the running example from the
method's original paper: the figure's graph, the queries the text highlights
and, when the paper prints them, the index labels. The runner
(`test_runner.py`) validates that the library's implementation reproduces all
of it, in three layers:

1. **Answers** — every pair `(u, v)` of the transcribed graph;
2. **Highlighted queries** — the pairs the paper's text discusses;
3. **Printed labels** — the built index matches the figure (when available).

## How to fill in a stub

1. Open the PDF and figure named in the file's header.
2. Follow the header's numbered steps (edges → num_nodes → queries → labels).
3. Run `pytest tests/paper_examples/test_runner.py -k <method> -v`.
4. Interpret a failure:
   - **"transcription error"** = graph/labels mis-copied — re-check the figure;
   - **any other failure** = a possible fidelity bug in the library (report it!).

Tip: when the figure labels vertices with letters, map letters → integers
(alphabetical order) and note the mapping in a comment inside the stub.

## How to create a stub for a method without one

Copy `hl.py` (the filled reference example), adjust `method` (the `catalog`
key), the provenance (`source`, `figure`, `doi`) and the instruction header.
Unfilled stubs (empty `edges`) show up as SKIP — they never break CI. Methods
still without a stub: GRAIL, PLL, TOL, TFLabel, BFL, ChainCover, TreeSSPI and
the baselines (TC, BFSDFS — textbook methods without a running-example figure).

## Labels (Layer 3)

Only methods with introspection implemented support `labels` (today: `hl`, with
`kind="two_hop"` via `HL.two_hop_labels()`). If your method's index does not
fit any existing `kind`, the escape hatches are (in order):

1. a new `kind` + comparator in `_comparators.py`;
2. `mode="invariant"` (the built labels only need to induce the same
   reachability as the paper's);
3. omit `labels` — Layers 1–2 already validate the method.

Every comparator first runs the **transcription cross-check**: the reachability
implied by the labels copied from the paper must match the one derived from the
copied edges. A mismatch means a data-entry error in the transcription, and the
failure message points at the exact conflicting pairs.

## Provenance notes

- `docs/paper_166.pdf` is the FELINE paper (EDBT 2014); `docs/reneveloso.pdf`
  is the thesis (144 pp.) — use the paper.
- `docs/scarab.pdf` (SCARAB, SIGMOD 2012) is a supporting reference for HL
  (the FastCover backbone); it has no stub of its own.
- In `docs/ferrari.pdf` the figure captions extract on p. 10 of this PDF
  version; the figures themselves appear earlier.
