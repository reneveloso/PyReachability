#!/usr/bin/env bash
# Fetch standard reachability benchmark DAGs into benchmarks/data/ (which is gitignored).
#
# The SIGMOD'08 small/medium real DAGs (amaze, kegg, agrocyc, ... ) are the de-facto standard
# graphs in the reachability literature. They ship inside the public GRAIL reference repository
# (github.com/zakimjz/grail, Downloads/sigmod08.tar.gz). This script clones that repo shallowly,
# extracts the .gra files, and drops them in benchmarks/data/. The large cit-Patents graph (for the
# scalable methods) is fetched separately by the same repo's Downloads if not already present.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
data="$here/data"
mkdir -p "$data"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "Cloning GRAIL reference repo (shallow) for benchmark datasets..."
git clone --depth 1 https://github.com/zakimjz/grail "$tmp/grail" >/dev/null 2>&1

echo "Extracting SIGMOD'08 DAGs..."
tar xzf "$tmp/grail/Downloads/sigmod08.tar.gz" -C "$tmp"
cp "$tmp"/sigmod08/*.gra "$data/"

# Large graph for the scalable methods (optional; ~68 MB).
if [ ! -f "$data/cit-Patents.scc.gra.gz" ] && [ -f "$tmp/grail/Downloads/cit-Patents.scc.gra.gz" ]; then
  cp "$tmp/grail/Downloads/cit-Patents.scc.gra.gz" "$data/"
fi

echo "Datasets in $data:"
ls -1 "$data"
