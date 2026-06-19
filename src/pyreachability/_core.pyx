# distutils: language = c++
# cython: language_level=3
cimport numpy as cnp
import numpy as np
from libcpp.vector cimport vector
from ._core cimport CSRGraph, vid_t, bfs_reaches

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
        """Build a graph by reading an edge list from a text file.

        Each non-empty, non-comment line holds an edge as two integers
        ``u v`` (whitespace-separated). Blank lines and lines starting with
        ``#`` are ignored. ``num_nodes`` is inferred as ``max(id) + 1``.

        Parameters
        ----------
        path : str
            Path to the file.
        fmt : str, optional
            Input format. Currently only ``"edgelist"`` is supported.

        Returns
        -------
        Graph

        Raises
        ------
        ValueError
            If ``fmt`` is unsupported, or a line is malformed (the error
            message includes the 1-based line number).
        """
        if fmt != "edgelist":
            raise ValueError(f"unsupported fmt: {fmt!r}")
        srcs = []; dsts = []; n = 0
        with open(path, "r") as fh:
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
