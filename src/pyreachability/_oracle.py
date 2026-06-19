"""Pure-Python reachability oracle — independent ground truth for tests."""


def reachable_set(num_nodes, edges):
    """Return {u: set of vertices reachable from u}, reflexive, via DFS per source."""
    adj = {u: set() for u in range(num_nodes)}
    for a, b in edges:
        if a != b:
            adj[a].add(b)
    reach = {}
    for s in range(num_nodes):
        seen = {s}
        stack = [s]
        while stack:
            x = stack.pop()
            for w in adj[x]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        reach[s] = seen
    return reach


def oracle_query(reach, u, v):
    """True iff v is reachable from u (reflexive)."""
    return v in reach[u]
