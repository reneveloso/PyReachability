# Verbatim paper examples (fidelity suite)

*Guia em português: [README_pt.md](README_pt.md).*

Each `<method>.py` file in this folder transcribes the **running example from
the method's original paper**: the figure's graph, the queries the text
highlights and, when the paper prints them, the index labels. The runner
(`test_runner.py`) validates that the library's implementation reproduces all
of it, in three layers:

| Layer | What is checked | Required? |
|---|---|---|
| 1 — Answers | `query(u, v)` for **every** pair of the transcribed graph | always |
| 2 — Highlighted queries | the specific pairs the paper's text discusses | if `queries` given |
| 3 — Printed labels | the built index matches the paper's label figure | if `labels` given |

The filled reference example is [`hl.py`](hl.py) — read it once before filling
your first stub.

## Quick start

```bash
# run the whole suite (unfilled stubs SKIP, they never fail)
pytest tests/paper_examples/ -v

# run a single method's example
pytest tests/paper_examples/test_runner.py -k treecover -v
```

An **unfilled** stub reports (real output):

```
SKIPPED [1] tests/paper_examples/test_runner.py:44: stub 'treecover' not
filled yet (edges empty) — see README.md in this folder
```

A **filled and passing** stub reports:

```
tests/paper_examples/test_runner.py::test_paper_example[hl] PASSED
```

## Anatomy of a stub

```python
from _schema import PaperExample, LabelCheck   # LabelCheck only if you use Layer 3

EXAMPLE = PaperExample(
    method="treecover",          # the catalog key — catalog.methods() lists them
    source="Agrawal, Borgida, Jagadish, SIGMOD 1989 — ...",   # human-readable citation
    figure="Figure 3.3, p. 3",   # exactly which figure you transcribed
    doi="10.1145/67544.66950",
    num_nodes=5,                 # highest vertex id + 1
    edges=[(0, 1), (0, 2)],      # the figure's edges, verbatim, as (u, v) = u -> v
    queries=[(0, 2, True)],      # (u, v, expected) pairs the TEXT highlights
    labels=None,                 # or a LabelCheck — see "Layer 3" below
)
```

`reach` (optional) lets you hand-write the full ground truth; leave it out and
the runner derives reachability from `edges` by BFS — that is the normal case.

## Filling a stub, step by step

Suppose the paper's figure shows this 5-vertex DAG, with vertices labeled
`a..e` and arrows `a→b, a→c, b→d, c→d, d→e`:

**1. Map letters to integers** (alphabetical order) and note the mapping:

```python
    # vertex mapping: a=0, b=1, c=2, d=3, e=4
```

**2. Transcribe the edges** — one tuple per arrow, `(tail, head)`. Double-check
the *direction* of every arrowhead; a reversed edge is the most common mistake:

```python
    num_nodes=5,
    edges=[(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)],
```

**3. Copy the highlighted queries.** If the text says *"note that a reaches e
but e cannot reach a"*, that becomes:

```python
    queries=[(0, 4, True), (4, 0, False)],
```

**4. Run it:**

```bash
pytest tests/paper_examples/test_runner.py -k <method> -v
```

Layer 1 alone already checks all 25 pairs of this graph against the library.

## Layer 3: transcribing the paper's labels

Only add `labels` when the paper *prints* the built index in the figure **and**
the method has introspection support (today: `hl`, `kind="two_hop"`, via
`HL.two_hop_labels()`). Suppose the figure prints this label table for the DAG
above:

| v | Lin | Lout |
|---|-----|------|
| a | a   | a, b, c, d |
| e | d, e | e |

That becomes (with the letter mapping applied):

```python
    labels=LabelCheck(
        kind="two_hop",
        mode="invariant",        # see below for exact vs invariant
        expected={
            0: {"Lin": {0}, "Lout": {0, 1, 2, 3}},
            4: {"Lin": {3, 4}, "Lout": {4}},
        },
    ),
```

Notes:

- **Partial tables are fine.** If the figure prints only some vertices (or has
  a `...` row), transcribe only those — the comparison restricts itself to the
  transcribed vertices automatically.
- **`mode="exact"` vs `mode="invariant"`.** `exact` demands the built labels
  equal the printed ones set-for-set — only possible when the paper fixes the
  construction order completely. `invariant` demands the built labels *induce
  the same reachability* as the printed ones (the right choice when the
  algorithm has tie-breaking freedom, e.g. HL's FastCover backbone). When in
  doubt, start with `exact`; if it fails while the cross-check passes, switch
  to `invariant` and say why in a comment.

### How labels decide reachability (the 2-hop rule)

`u` reaches `v` **iff** `Lout(u) ∩ Lin(v) ≠ ∅`. In the mini table above:
`Lout(a) = {a,b,c,d}` and `Lin(e) = {d,e}` intersect at `{d}`, so `a` reaches
`e` — matching the graph (`a→b→d→e`). This rule is what the cross-check and
the `invariant` mode compute.

## Interpreting failures

**"transcription error"** — the graph and the labels you typed disagree with
each other. Real message from a deliberately broken stub:

```
AssertionError: [hl] Fig. X: transcription error (graph or labels mis-copied
from the paper). Reachability from the transcribed edges and from the
transcribed labels disagree on: [(0, 2)]
```

The listed pairs tell you where to look: here, edges say `0` reaches `2` but
the transcribed labels say it does not (or vice versa). Re-open the figure and
fix whichever you mis-copied. The library is not involved in this check at
all — it compares your two transcriptions against each other.

**Layer 1/2 failure** (`query(u,v) = X, paper graph says Y`) — the
transcriptions are consistent but the *implementation* disagrees with the
paper's example. First re-check the figure once more; if the transcription is
right, you may have found a **fidelity bug** — open an issue with the stub.

**Layer 3 `exact` mismatch with a passing cross-check** — usually not a bug:
the construction made different (but valid) tie-breaking choices than the
paper's run. Switch to `mode="invariant"` and note why.

## Creating a stub for a method that has none

Methods still without a stub: GRAIL, PLL, TOL, TFLabel, BFL, ChainCover,
TreeSSPI, and the baselines (TC, BFSDFS — textbook methods, no running-example
figure). To add one:

1. Get the paper's PDF and find the running-example figure (usually named
   "Figure 1/2 … example").
2. Copy any unfilled stub (e.g. `treecover.py`), rename to `<catalog-key>.py` —
   the runner discovers any new `*.py` automatically (names starting with `_`,
   `test_` or `conftest` are excluded).
3. Update `method`, `source`, `figure`, `doi` and the instruction header.
4. Fill it following the steps above; unfilled it just SKIPs, so committing a
   provenance-only stub is fine.

Checklist before committing a filled stub:

- [ ] every arrowhead direction double-checked;
- [ ] letter→integer mapping (if any) noted in a comment;
- [ ] `pytest ... -k <method> -v` passes;
- [ ] hard-to-read edges flagged in a comment for human review
      (see the `CAUTION` block in `hl.py` for the pattern).

## Adding a new label kind (comparators)

If a paper prints an index that fits no existing `kind` (intervals, 2D
coordinates, chains, ...): add a comparator function to `_comparators.py`,
register it in `COMPARATORS`, and expose matching introspection on the
implementation (see `HL.two_hop_labels()` for the pattern — a read-only method,
original-vertex space, DAG inputs). Every comparator must run a transcription
cross-check before touching the implementation. The escape hatches, in order:
new kind → `mode="invariant"` → omit `labels` (Layers 1–2 still validate the
method).

## Provenance notes

- `docs/paper_166.pdf` is the FELINE paper (EDBT 2014); `docs/reneveloso.pdf`
  is the thesis (144 pp.) — use the paper.
- `docs/scarab.pdf` (SCARAB, SIGMOD 2012) is a supporting reference for HL
  (the FastCover backbone); it has no stub of its own.
- In `docs/ferrari.pdf` the figure captions extract on p. 10 of this PDF
  version; the figures themselves appear earlier.
- Tip for dense figures: render at high resolution and read quadrant by
  quadrant, e.g. `pdftoppm -f 5 -l 5 -r 600 -png docs/DL.pdf /tmp/fig`.
