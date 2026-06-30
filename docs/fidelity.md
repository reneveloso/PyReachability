# Fidelity to the source publications

PyReachability aims to be a *faithful* implementation of each published method: same algorithmic
idea, same index semantics, same query answers. **Every method is validated for exact correctness
against the BFS/DFS oracle** (property-based tests, hundreds of random graphs each), so no method
ever returns a wrong reachability answer.

Where an implementation departs from the paper, the departure is one of three kinds:

- **Faithful** — the construction and the produced index match the paper (up to tie-breaking).
- **(B) Speed-only** — the produced index / query answers are equivalent to the paper, but a
  construction or query *subroutine* is the simpler textbook version rather than the paper's
  engineered one (slower, but same result). Often the paper itself offers the simpler option.
- **(A) Index differs** — the produced index differs in *size/structure* from the paper's
  (queries still exact), because a construction *choice* (which spanning tree, which dummy
  scheme, which parameter) was simplified.

This page documents every (A) and (B) deviation so users know exactly what they get. Methods not
listed (BFS/DFS, TC, Tree Cover, GRAIL, FELINE, PLL, BFL, Chain Cover, TOL, DL) are faithful.

## Summary

| Method | Paper's construction / structure | Our implementation | Deviation |
|---|---|---|---|
| 2-Hop | greedy set cover; densest subgraph by linear 2-approx | same, but center graphs rebuilt each round (no incremental) | (B) speed |
| 3-Hop | TC contour + factorization; rank-subgraph densest search (§4.3); O(log²) segment query | linear 2-approx densest (paper's own baseline) + linear segment lookup | (B) speed |
| TFL | topological folding with lazily-created **shared** dummy vertices (Procedure 1) | Procedure 1 (shared lazy dummies) | faithful |
| HL | recursive backbone with ε=2 (FastCover) | ε=1 backbone (= vertex cover; ε is a paper parameter) | (A) larger labels |
| O'Reach | supportive-vertex selection (slim/central strategy); seed pruning; pruned bidirectional BFS fallback | central-level selection; no seed pruning; guided-DFS fallback | (A) labels + (B) speed |
| Path-Hop | **optimal** tree cover + multi-interval labeling | Agrawal optimal tree cover; greedy whole-Pred/Succ hop density | (B) slow build |
| Ferrari | Ferrari-L **and** Ferrari-G (global budget); seed + topological pruning | Ferrari-L only; topological-level pruning | (A) variant + (B) speed |
| Dual-labeling | a spanning tree + minimal-equivalent-graph reduction (§5); O(1) TLC counting via gridding/snapping | minimal-equivalent-graph + DFS spanning tree; O(t) link-table scan | (B) query speed |
| Tree+SSPI | tree-cover via **DFS traversal**; SSPI | DFS tree-cover; SSPI (inheritance resolved at query) | (B) query speed |
| GRIPP | hop technique + advanced 4-case pruning | hop technique + basic hop-node pruning | (B) speed |
| Path-Tree | **Edmonds** max-weight SP-tree; minimal-equivalent-edge-set; O(log²k) query | greedy spanning arborescence; all SP-tree-pair edges; linear residual scan | (A) larger index + (B) speed |
| IP | k-min-wise labels + level helper + **interval** helper | k-min-wise + level helper (interval helper omitted) | (B) speed |
| PReaCH | contraction hierarchies + Lemmas 2–7 pruning | Lemmas 2–4; Lemmas 5–7 omitted | (B) speed |
| Optimal Chain Cover | minimum chains via **O(n²+bn√b)** stratification + virtual-node matching | minimum chains via textbook **Kuhn** matching | (B) speed (same minimum) |

## Notes per deviation

**2-Hop (Cohen, Halperin, Kaplan, Zwick, 2003).** The paper casts minimum 2-hop as a set cover and
selects, each round, the center whose center-graph has the densest subgraph, approximated by the
linear-time 2-approximation (drop the min-degree vertex, keep the densest snapshot). We implement
exactly that approximation. We rebuild all center graphs every round instead of maintaining them
incrementally, so construction is slower — but minimum 2-hop is NP-hard and its construction is
famously expensive in the literature (PLL/TFL/DL/TOL exist precisely as cheaper heuristics), so this
is the method's known character, not a change to the produced cover.

**3-Hop (Jin, Xiang, Ruan, Fuhry, 2009).** Construction = TC contour + greedy factorization whose
core is a densest-subgraph search. The paper presents the linear 2-approximation as the baseline and
a faster rank-subgraph search (§4.3) as an optimization; we use the 2-approximation baseline. Queries
use a per-chain anchor segment lookup rather than the paper's O(log²) structure. The survey notes
3-Hop's indexing cost is inherently high ("less applicable" to large graphs).

**HL (Jin & Wang, 2013).** The locality threshold ε is a parameter; the paper focuses on ε=2 with the
FastCover backbone. We use ε=1, for which the backbone is exactly a vertex cover. Same hierarchy +
Algorithm 1 propagation; labels are **larger** than the ε=2 version.

**O'Reach (Hanauer, Schulz, Trummer, 2021).** Topological levels, supportive vertices (full R⁺/R⁻),
and extended topological orderings are implemented faithfully. The supportive-vertex *selection* uses
a simplified central-level heuristic (the paper's strategy is tunable), the optional seed-pruning
labels are omitted, and the fallback is a guided DFS rather than the paper's pruned bidirectional
BFS. Same observations, same answers.

**Spanning structure per paper (verified).** The tree-cover-family methods differ in which tree the
*authors* use, so we follow each one:
- **Tree Cover (Agrawal, 1989)** and **Path-Hop (Cai & Poon, 2010)** use Agrawal's *optimum tree
  cover* (Path-Hop reuses Agrawal's multi-interval labeling). We build exactly that (shared
  `optimal_tree_parent`: each node's tree parent is the in-neighbour with the largest predecessor
  set). Faithful.
- **Tree+SSPI (Chen et al., 2005)** builds its tree-cover by a *depth-first traversal*; we use a DFS
  tree-cover too. Faithful tree; the only deviation is that we store each vertex's own non-tree
  predecessors and resolve the paper's predecessor *inheritance* at query time (same answers).
- **Dual-labeling (Wang et al., 2006)** uses "a spanning tree" (no specific algorithm mandated; we
  use DFS) over the §5 *minimal-equivalent-graph* (the unique transitive reduction of the DAG), which
  we now compute to shrink the non-tree edge set `t`. The remaining deviation is query-side: we scan
  the link table in O(t) instead of the paper's O(1) gridding/snapping counter (same answers).
- **Path-Tree (Jin et al., 2011)** uses an *Edmonds maximum-weight* SP-tree over the path-graph plus
  the *minimal equivalent edge set*; we use a greedy spanning arborescence and all SP-tree-pair
  edges, so the residual/index is larger. Query scans the residual linearly (vs the paper's
  O(log²k)).

**Ferrari (Seufert et al., 2013).** We implement the per-vertex-budget variant (Ferrari-L), one of the
paper's two variants, plus the topological-level filter. The global-budget variant (Ferrari-G) and
the optional seed-vertex pruning are omitted.

**GRIPP (Trißl & Leser, 2007).** The hop technique is faithful; the paper's advanced relative-position
pruning (four cases, ascending-preorder traversal) is omitted — a query-speed optimization only.

**IP (Wei, Yu, Lu, 2014).** k-min-wise permutation labels and the topological-level helper are
implemented; the second helper label (an interval, to further cut DFS) is omitted. Same answers.

**PReaCH (Merz & Sanders, 2014).** Contraction-hierarchy ordering, forward/backward levels, and the
single-DFS interval cuts (Lemmas 2–4) are implemented; the extra empty/full ranges of Lemmas 5–7 are
omitted — they sharpen pruning, not correctness.

**Optimal Chain Cover (Chen & Chen, 2008).** The produced index is identical to the paper's: the
*minimum* chain decomposition (verified to equal the Dilworth width). The paper computes it with an
engineered O(n²+bn√b) stratification + virtual-node matching; we use textbook Kuhn maximum bipartite
matching over the reachability relation (slower build, same minimum chains).
