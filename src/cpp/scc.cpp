#include "reachability/scc.hpp"
#include <algorithm>
#include <stack>

namespace reachability {

Condensation scc_condense(const CSRGraph& g) {
    const vid_t n = g.num_nodes();
    Condensation c;
    c.comp.assign(n, -1);

    std::vector<vid_t> index(n, -1), low(n, 0);
    std::vector<char> on_stack(n, 0);
    std::vector<vid_t> tarjan_stack;
    vid_t idx = 0;
    vid_t comp_count = 0;

    // Iterative Tarjan: each frame tracks the current out-neighbor cursor.
    std::vector<vid_t> call;                 // vertex stack
    std::vector<const vid_t*> cursor;        // next neighbor pointer per frame

    for (vid_t s = 0; s < n; ++s) {
        if (index[s] != -1) continue;
        call.push_back(s);
        cursor.push_back(g.out_begin(s));
        index[s] = low[s] = idx++;
        tarjan_stack.push_back(s);
        on_stack[s] = 1;

        while (!call.empty()) {
            vid_t v = call.back();
            const vid_t* end = g.out_end(v);
            bool recursed = false;
            while (cursor.back() != end) {
                vid_t w = *cursor.back();
                ++cursor.back();
                if (index[w] == -1) {
                    index[w] = low[w] = idx++;
                    tarjan_stack.push_back(w);
                    on_stack[w] = 1;
                    call.push_back(w);
                    cursor.push_back(g.out_begin(w));
                    recursed = true;
                    break;
                } else if (on_stack[w]) {
                    low[v] = std::min(low[v], index[w]);
                }
            }
            if (recursed) continue;

            if (low[v] == index[v]) {        // root of an SCC
                while (true) {
                    vid_t w = tarjan_stack.back();
                    tarjan_stack.pop_back();
                    on_stack[w] = 0;
                    c.comp[w] = comp_count;
                    if (w == v) break;
                }
                ++comp_count;
            }
            call.pop_back();
            cursor.pop_back();
            if (!call.empty()) {
                low[call.back()] = std::min(low[call.back()], low[v]);
            }
        }
    }
    c.num_comp = comp_count;

    // Tarjan numbers SCCs in reverse topological order; reverse to get topo order.
    // Build condensed DAG edges between distinct components.
    std::vector<vid_t> csrc, cdst;
    for (vid_t u = 0; u < n; ++u) {
        for (const vid_t* it = g.out_begin(u); it != g.out_end(u); ++it) {
            vid_t cu = c.comp[u], cv = c.comp[*it];
            if (cu != cv) { csrc.push_back(cu); cdst.push_back(cv); }
        }
    }
    c.dag = CSRGraph(comp_count, csrc, cdst);

    // Topological order of components: reverse of Tarjan completion order.
    // comp ids 0..comp_count-1 were assigned in reverse-topo; so topo = descending id.
    c.topo_order.resize(comp_count);
    for (vid_t i = 0; i < comp_count; ++i)
        c.topo_order[i] = comp_count - 1 - i;

    return c;
}

}  // namespace reachability
