#!/bin/sh
# Preview the site exactly as GitHub Pages will serve it.
#
#   ./tools/serve.sh          -> http://localhost:8000
#   ./tools/serve.sh 8080     -> http://localhost:8080
#
# Opening index.html as a file:// URL does NOT work: directory links like
# "experience/" need a server to resolve to experience/index.html, and the
# brand link "/" means the site root, which file:// reads as your disk root.
cd "$(dirname "$0")/.." || exit 1
PORT="${1:-8000}"
echo "Serving $(pwd) at http://localhost:$PORT  (Ctrl+C to stop)"
exec python3 -m http.server "$PORT"
