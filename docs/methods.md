# Method catalog & coverage

PyReachability's method list is **not arbitrary**: it follows the peer-reviewed survey

> Chao Zhang, Angela Bonifati, M. Tamer Özsu. *Indexing Techniques for Graph Reachability
> Queries.* ACM Computing Surveys 58(6), Article 156, 2025. DOI `10.1145/3776737`.
> (Preliminary tutorial: *An Overview of Reachability Indexes on Graphs*, SIGMOD-Companion
> 2023, DOI `10.1145/3555041.3589408`.)

**Goal:** implement the survey's **plain-reachability** indexes (Table 1) under one common
interface and benchmark harness. The catalog is extensible — each method is a plug-in — so
coverage grows over releases. Edge-labeled / path-constrained (LCR) indexes (the survey's
Table 2) are a planned later extension.

Inclusion rule: a method enters the library only if it has a peer-reviewed publication; we
read its paper (and reference implementation, when one exists) before porting it.

## Plain-reachability indexes (CSUR 2025, Table 1)

Status: ✅ implemented · ⬜ planned. Each method is classified by the survey's index class.

### Baselines (survey §2.2)
- ✅ **BFS/DFS** — online traversal (correctness oracle).
- ✅ **TC** — full transitive closure (bitset). Warshall, JACM 1962.

### Tree Cover class
- ✅ **Tree Cover** — Agrawal, Borgida, Jagadish, SIGMOD 1989.
- ✅ **GRAIL** — Yıldırım, Chaoji, Zaki, PVLDB 2010 (+ PP, level filter, bidirectional).
- ✅ **Tree+SSPI** — Chen, Gupta, Kurul, VLDB 2005 (tree-cover + surrogate/surplus predecessor index).
- ✅ **Dual labeling** — Wang, He, Yang, Yu, Yu, ICDE 2006 (tree intervals + transitive link table).
- ✅ **GRIPP** — Trißl & Leser, SIGMOD 2007 (pre/postorder order-tree instances + hop technique).
- ✅ **Path-tree** — Jin, Ruan, Xiang, Wang, ACM TODS 2011 (path-tree cover + 3-tuple labeling + residual TC).
- ✅ **Ferrari** — Seufert, Anand, Bedathur, Weikum, ICDE 2013 (budgeted exact/approx intervals + guided search).
- ⬜ **DAGGER** (dynamic)

### 2-Hop class
- ✅ **PLL** — Yano, Akiba, Iwata, Yoshida, CIKM 2013.
- ✅ **2-Hop** — Cohen, Halperin, Kaplan, Zwick, SIAM J. Comput. 2003 (greedy densest-subgraph cover).
- ✅ **3-Hop** — Jin, Xiang, Ruan, Fuhry, SIGMOD 2009 (TC contour + greedy factorization).
- ⬜ **U2-hop**
- ✅ **Path-hop** — Cai & Poon, CIKM 2010 (residual TC + greedy path-hop set cover; trees as highways).
- ✅ **TFL** (Topological Folding Labeling) — Cheng, Huang, Wu, Fu, SIGMOD 2013.
- ✅ **DL** (Distribution Labeling) — Jin & Wang, PVLDB 2013 (Algorithm 2; survey-proven equivalent to PLL).
- ✅ **HL** (Hierarchical Labeling) — Jin & Wang, PVLDB 2013 (recursive reachability backbone).
- ✅ **TOL** (Total Order Labeling) — Zhu, Lin, Wang, Xiao, SIGMOD 2014 (contribution-score order).
- ⬜ **DBL** (dynamic)
- ✅ **O'Reach** — Hanauer, Schulz, Trummer, SEA 2021 (constant-time observations + guided fallback).
- ⬜ **Ralf et al.** (dynamic 2-hop)

### Approximate TC class
- ✅ **IP** (Independent Permutation) — Wei, Yu, Lu, PVLDB 2014 (k-min-wise permutation labels + guided DFS).
- ✅ **BFL** (Bloom Filter Labeling) — Su, Zhu, Wei, Yu, TKDE 2017.

### Chain Cover class
- ✅ **Chain Cover** — Jagadish, ACM TODS 1990 (greedy chain decomposition).
- ✅ **Optimal Chain Cover** — Chen & Chen, ICDE 2008 (minimum chains via max bipartite matching / Dilworth).

### Other
- ✅ **FELINE** — Veloso, Cerf, Meira Jr., Zaki, EDBT 2014 (canonical reference impl).
- ✅ **PReaCH** — Merz & Sanders, ESA 2014 (ported from paper; oracle-verified).

## Status summary

Implemented: 7 (BFS/DFS, TC, Tree Cover, GRAIL, FELINE, PLL, BFL). Phase 2 has begun: BFL
(Approximate TC) is the first of the expansion, verified against the author's reference
implementation (github.com/BoleynSu/bfl) on a 200k-query set. The remaining Table-1 methods
follow. Exact citations are taken from CSUR 2025 Table 1 and confirmed against the primary
source at implementation time.
