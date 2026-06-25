# distutils: language = c++
# cython: language_level=3
cimport numpy as cnp
import numpy as np
import gzip
import array as _pyarray
from libcpp.vector cimport vector
from ._core cimport CSRGraph, vid_t, bfs_reaches, Condensation, scc_condense, Grail, Feline, PLL, TC, TreeCover, BFL, ChainCover, PReaCH, TwoHop, TFLabel, TOL, HL, OReach, ThreeHop, PathHop, Ferrari

cnp.import_array()


def ping():
    return "pong"


cdef class Graph:
    """A directed graph stored internally as CSR (Compressed Sparse Row).

    Build a graph with :meth:`from_edges` (NumPy arrays) or :meth:`from_file`
    (edge-list text). Self-loops are dropped and parallel edges deduplicated,
    since neither affects reachability. Vertex ids are 0-based ``int32``.

    Pass a ``Graph`` to a method's ``build`` (e.g. :class:`~pyreachability.BFSDFS`).
    """
    cdef CSRGraph* _g

    def __cinit__(self):
        self._g = NULL

    def __dealloc__(self):
        if self._g != NULL:
            del self._g

    cdef CSRGraph* _ptr(self):
        return self._g

    @staticmethod
    def from_edges(src, dst=None, num_nodes=None):
        """Build a graph from edges, in either of two forms.

        Two-array form::

            Graph.from_edges(src, dst, num_nodes)

        Single-array form (an ``(E, 2)`` array of ``[u, v]`` rows)::

            Graph.from_edges(edges, num_nodes=...)

        Parameters
        ----------
        src : array_like of int
            Either the per-edge source ids (two-array form) or, when ``dst`` is
            omitted, an ``(E, 2)`` array whose rows are ``[u, v]`` edges.
        dst : array_like of int, optional
            Per-edge destination ids (two-array form). Must have the same length
            as ``src``. Omit it to use the single-array form.
        num_nodes : int
            Number of vertices (required, keyword-friendly). All ids must lie in
            ``[0, num_nodes)``.

        Returns
        -------
        Graph

        Raises
        ------
        TypeError
            If ``num_nodes`` is not given.
        ValueError
            If ``src`` and ``dst`` have different lengths, or the single-array
            form is not shaped ``(E, 2)``.
        IndexError
            If any endpoint is outside ``[0, num_nodes)``.
        """
        if num_nodes is None:
            raise TypeError("from_edges() requires num_nodes")
        if dst is None:
            edges = np.ascontiguousarray(src, dtype=np.int32)
            if edges.ndim != 2 or edges.shape[1] != 2:
                raise ValueError(
                    "single-array form requires an (E, 2) int array; "
                    "otherwise pass both src and dst")
            src = edges[:, 0]
            dst = edges[:, 1]
        cdef cnp.ndarray[cnp.int32_t, ndim=1] s = np.ascontiguousarray(src, dtype=np.int32)
        cdef cnp.ndarray[cnp.int32_t, ndim=1] d = np.ascontiguousarray(dst, dtype=np.int32)
        if s.shape[0] != d.shape[0]:
            raise ValueError("src and dst must have equal length")
        cdef int n = int(num_nodes)
        cdef Py_ssize_t m = s.shape[0], i
        for i in range(m):
            if s[i] < 0 or s[i] >= n or d[i] < 0 or d[i] >= n:
                raise IndexError("edge endpoint out of range [0, num_nodes)")
        cdef vector[vid_t] cs, cd
        cs.reserve(m); cd.reserve(m)
        for i in range(m):
            cs.push_back(s[i]); cd.push_back(d[i])
        cdef Graph g = Graph()
        g._g = new CSRGraph(n, cs, cd)
        return g

    @staticmethod
    def from_file(path, fmt="edgelist"):
        """Build a graph by reading it from a file.

        Files ending in ``.gz`` are transparently decompressed.

        Parameters
        ----------
        path : str
            Path to the file (optionally gzipped).
        fmt : str, optional
            Input format:

            - ``"edgelist"`` (default): one edge per line as ``u v``
              (whitespace-separated). Blank lines and ``#`` comments are
              ignored; ``num_nodes`` is inferred as ``max(id) + 1``.
            - ``"gra"``: the GRAIL/GREACH adjacency format — an optional
              ``graph_for_greach`` header line, then the vertex count, then
              one line per vertex ``id: succ1 succ2 ... #``. The declared
              vertex count is used (so isolated/sink vertices are kept).

        Returns
        -------
        Graph

        Raises
        ------
        ValueError
            If ``fmt`` is unsupported, or the file is malformed.
        """
        opener = gzip.open if str(path).endswith(".gz") else open
        if fmt == "edgelist":
            srcs = []; dsts = []; n = 0
            with opener(path, "rt") as fh:
                for lineno, raw in enumerate(fh, start=1):
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) < 2:
                        raise ValueError(f"malformed edge at line {lineno}: {raw!r}")
                    try:
                        u = int(parts[0]); v = int(parts[1])
                    except ValueError:
                        raise ValueError(f"malformed edge at line {lineno}: {raw!r}")
                    srcs.append(u); dsts.append(v)
                    n = max(n, u + 1, v + 1)
            return Graph.from_edges(np.asarray(srcs, dtype=np.int32),
                                    np.asarray(dsts, dtype=np.int32), num_nodes=n)
        elif fmt == "gra":
            # array('i') keeps memory compact on the large graphs this format is used for.
            srcs = _pyarray.array("i"); dsts = _pyarray.array("i")
            n = -1
            with opener(path, "rt") as fh:
                for raw in fh:
                    line = raw.strip()
                    if not line:
                        continue
                    if n < 0:
                        if line.isdigit():        # vertex count
                            n = int(line)
                        # else: header marker (e.g. "graph_for_greach") -> skip
                        continue
                    head, sep, rest = line.partition(":")
                    if not sep:
                        continue
                    try:
                        u = int(head)
                    except ValueError:
                        raise ValueError(f"malformed .gra adjacency line: {raw!r}")
                    for tok in rest.split():
                        if tok == "#":
                            break
                        srcs.append(u); dsts.append(int(tok))
            if n < 0:
                raise ValueError("missing vertex count in .gra file")
            return Graph.from_edges(np.frombuffer(srcs, dtype=np.int32),
                                    np.frombuffer(dsts, dtype=np.int32), num_nodes=n)
        else:
            raise ValueError(f"unsupported fmt: {fmt!r}")

    def to_edges(self):
        """Return the graph's edges as two int32 arrays ``(src, dst)``.

        Reconstructed from the internal CSR, so edges are deduplicated, free of
        self-loops, and grouped/sorted by source. Inverse of :meth:`from_edges`.

        Returns
        -------
        tuple of numpy.ndarray
            ``(src, dst)``, each of length ``num_edges`` and dtype ``int32``.
        """
        cdef int n = self._g.num_nodes()
        cdef size_t m = self._g.num_edges()
        cdef cnp.ndarray[cnp.int32_t, ndim=1] src = np.empty(m, dtype=np.int32)
        cdef cnp.ndarray[cnp.int32_t, ndim=1] dst = np.empty(m, dtype=np.int32)
        cdef size_t idx = 0
        cdef int u
        cdef const vid_t* it
        cdef const vid_t* end
        for u in range(n):
            it = self._g.out_begin(u)
            end = self._g.out_end(u)
            while it != end:
                src[idx] = u
                dst[idx] = it[0]
                it += 1
                idx += 1
        return src, dst

    @property
    def num_nodes(self):
        """int: Number of vertices in the graph."""
        return self._g.num_nodes()

    @property
    def num_edges(self):
        """int: Number of edges after dropping self-loops and duplicates."""
        return self._g.num_edges()


cdef class _BFSDFSCore:
    cdef Graph _graph

    def __cinit__(self):
        self._graph = None

    def build(self, Graph graph):
        self._graph = graph

    def query(self, int u, int v):
        if self._graph is None:
            raise RuntimeError("index not built")
        cdef int n = self._graph._g.num_nodes()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        return bfs_reaches(self._graph._g[0], u, v)

    def query_batch(self, pairs):
        if self._graph is None:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = self._graph._g.num_nodes()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef CSRGraph* g = self._graph._g
        with nogil:
            for i in range(m):
                ov[i] = 1 if bfs_reaches(g[0], pv[i, 0], pv[i, 1]) else 0
        return out.view(np.bool_)


cdef class _GRAILCore:
    cdef Grail* _grail
    cdef vector[vid_t] _comp
    cdef int _d
    cdef unsigned int _seed
    cdef bint _bidir
    cdef bint _built

    def __cinit__(self, int d=5, unsigned int seed=1, bint bidirectional=False):
        self._grail = new Grail()
        self._d = d
        self._seed = seed
        self._bidir = bidirectional
        self._built = False

    def __dealloc__(self):
        if self._grail != NULL:
            del self._grail

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._grail.build(cond.dag, self._d, self._seed, self._bidir)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._grail.reaches(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef Grail* gr = self._grail
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if gr.reaches(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._grail.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _FelineCore:
    cdef Feline* _feline
    cdef vector[vid_t] _comp
    cdef bint _bidir
    cdef bint _built

    def __cinit__(self, bint bidirectional=False):
        self._feline = new Feline()
        self._bidir = bidirectional
        self._built = False

    def __dealloc__(self):
        if self._feline != NULL:
            del self._feline

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._feline.build(cond.dag, self._bidir)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._feline.reaches(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef Feline* fe = self._feline
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if fe.reaches(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._feline.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _PLLCore:
    cdef PLL* _pll
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._pll = new PLL()
        self._built = False

    def __dealloc__(self):
        if self._pll != NULL:
            del self._pll

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._pll.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._pll.query(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef PLL* pl = self._pll
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if pl.query(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._pll.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _TCCore:
    cdef TC* _tc
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._tc = new TC()
        self._built = False

    def __dealloc__(self):
        if self._tc != NULL:
            del self._tc

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._tc.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._tc.query(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef TC* tc = self._tc
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if tc.query(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._tc.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _TreeCoverCore:
    cdef TreeCover* _tcv
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._tcv = new TreeCover()
        self._built = False

    def __dealloc__(self):
        if self._tcv != NULL:
            del self._tcv

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._tcv.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._tcv.query(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef TreeCover* tcv = self._tcv
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if tcv.query(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._tcv.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _BFLCore:
    cdef BFL* _bfl
    cdef vector[vid_t] _comp
    cdef int _k
    cdef unsigned int _seed
    cdef bint _built

    def __cinit__(self, int k=5, unsigned int seed=1):
        self._bfl = new BFL()
        self._k = k
        self._seed = seed
        self._built = False

    def __dealloc__(self):
        if self._bfl != NULL:
            del self._bfl

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._bfl.build(cond.dag, self._k, self._seed)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._bfl.reaches(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef BFL* bl = self._bfl
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if bl.reaches(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._bfl.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _ChainCoverCore:
    cdef ChainCover* _cc
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._cc = new ChainCover()
        self._built = False

    def __dealloc__(self):
        if self._cc != NULL:
            del self._cc

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._cc.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._cc.query(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef ChainCover* cc = self._cc
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if cc.query(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._cc.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _PReaCHCore:
    cdef PReaCH* _pr
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._pr = new PReaCH()
        self._built = False

    def __dealloc__(self):
        if self._pr != NULL:
            del self._pr

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._pr.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._pr.reaches(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef PReaCH* pr = self._pr
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if pr.reaches(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._pr.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _TwoHopCore:
    cdef TwoHop* _th
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._th = new TwoHop()
        self._built = False

    def __dealloc__(self):
        if self._th != NULL:
            del self._th

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._th.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._th.query(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef TwoHop* th = self._th
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if th.query(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._th.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _TFLabelCore:
    cdef TFLabel* _tf
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._tf = new TFLabel()
        self._built = False

    def __dealloc__(self):
        if self._tf != NULL:
            del self._tf

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._tf.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._tf.query(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef TFLabel* tf = self._tf
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if tf.query(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._tf.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _TOLCore:
    cdef TOL* _to
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._to = new TOL()
        self._built = False

    def __dealloc__(self):
        if self._to != NULL:
            del self._to

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._to.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._to.query(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef TOL* to = self._to
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if to.query(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._to.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _HLCore:
    cdef HL* _hl
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._hl = new HL()
        self._built = False

    def __dealloc__(self):
        if self._hl != NULL:
            del self._hl

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._hl.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._hl.query(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef HL* hl = self._hl
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if hl.query(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._hl.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _OReachCore:
    cdef OReach* _or
    cdef vector[vid_t] _comp
    cdef int _k
    cdef int _p
    cdef int _t
    cdef unsigned int _seed
    cdef bint _built

    def __cinit__(self, int k=16, int p=50, int t=4, unsigned int seed=1):
        self._or = new OReach()
        self._k = k
        self._p = p
        self._t = t
        self._seed = seed
        self._built = False

    def __dealloc__(self):
        if self._or != NULL:
            del self._or

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._or.build(cond.dag, self._k, self._p, self._t, self._seed)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._or.reaches(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef OReach* orr = self._or
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if orr.reaches(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._or.index_size_bytes() + self._comp.size() * sizeof(int)


cdef class _ThreeHopCore:
    cdef ThreeHop* _th
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._th = new ThreeHop()
        self._built = False

    def __dealloc__(self):
        if self._th != NULL:
            del self._th

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._th.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._th.query(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef ThreeHop* th = self._th
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if th.query(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._th.index_size_bytes() + self._comp.size() * sizeof(int)

cdef class _PathHopCore:
    cdef PathHop* _ph
    cdef vector[vid_t] _comp
    cdef bint _built

    def __cinit__(self):
        self._ph = new PathHop()
        self._built = False

    def __dealloc__(self):
        if self._ph != NULL:
            del self._ph

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._ph.build(cond.dag)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._ph.query(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef PathHop* ph = self._ph
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if ph.query(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._ph.index_size_bytes() + self._comp.size() * sizeof(int)

cdef class _FerrariCore:
    cdef Ferrari* _fr
    cdef vector[vid_t] _comp
    cdef int _k
    cdef bint _built

    def __cinit__(self, int k=2):
        self._fr = new Ferrari()
        self._k = k
        self._built = False

    def __dealloc__(self):
        if self._fr != NULL:
            del self._fr

    def build(self, Graph graph):
        cdef Condensation cond = scc_condense(graph._g[0])
        self._comp = cond.comp
        self._fr.build(cond.dag, self._k)
        self._built = True

    def query(self, int u, int v):
        if not self._built:
            raise RuntimeError("index not built")
        cdef int n = <int>self._comp.size()
        if u < 0 or u >= n or v < 0 or v >= n:
            raise IndexError("vertex id out of range")
        cdef vid_t cu = self._comp[u]
        cdef vid_t cv = self._comp[v]
        if cu == cv:
            return True
        return self._fr.reaches(cu, cv)

    def query_batch(self, pairs):
        if not self._built:
            raise RuntimeError("index not built")
        cdef cnp.ndarray[cnp.int32_t, ndim=2, mode="c"] p = \
            np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        cdef Py_ssize_t m = p.shape[0], i
        cdef cnp.ndarray[cnp.uint8_t, ndim=1] out = np.empty(m, dtype=np.uint8)
        cdef int n = <int>self._comp.size()
        if m and (int(p.min()) < 0 or int(p.max()) >= n):
            raise IndexError("vertex id out of range")
        cdef cnp.int32_t[:, ::1] pv = p
        cdef cnp.uint8_t[::1] ov = out
        cdef vector[vid_t]* comp = &self._comp
        cdef Ferrari* fr = self._fr
        cdef vid_t cu, cv
        with nogil:
            for i in range(m):
                cu = comp[0][pv[i, 0]]; cv = comp[0][pv[i, 1]]
                if cu == cv:
                    ov[i] = 1
                else:
                    ov[i] = 1 if fr.reaches(cu, cv) else 0
        return out.view(np.bool_)

    def index_size_bytes(self):
        return self._fr.index_size_bytes() + self._comp.size() * sizeof(int)
