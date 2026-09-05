#!/usr/bin/env bash
# Orivory one-command installer — the `npx claude-mem install` equivalent.
#
# Bootstraps the lite deployment (single container: SQLite + in-process
# Chroma) and, optionally, registers an agent client for auto-capture.
# Stdlib curl + docker only; everything idempotent.
#
#   curl -fsSL https://raw.githubusercontent.com/twilightt1/orivory/main/install.sh | bash
#
# Flags: --port 8000  --dir ~/.orivory  --with-capture --agent-name NAME
set -euo pipefail

PORT="8000"
DIR="${HOME}/.orivory"
IMAGE="ghcr.io/twilightt1/orivory:lite"
AGENT_NAME="openclaw-capture"
WITH_CAPTURE=0

say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --dir) DIR="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    --agent-name) AGENT_NAME="$2"; shift 2 ;;
    --with-capture) WITH_CAPTURE=1; shift ;;
    -h|--help)
      sed -n '2,9p' "$0"; exit 0 ;;
    *) warn "unknown flag: $1"; exit 2 ;;
  esac
done

command -v docker >/dev/null 2>&1 || { warn "docker is required: https://docs.docker.com/get-docker/"; exit 1; }

mkdir -p "$DIR"

say "pulling $IMAGE"
docker pull -q "$IMAGE" >/dev/null

say "starting Orivory (lite) on :$PORT — data in $DIR"
docker rm -f orivory-lite >/dev/null 2>&1 || true
docker run -d --name orivory-lite \
  -p "$PORT":8000 \
  -v "$DIR/data:/data" \
  --restart unless-stopped \
  -e ORIVORY_LITE=1 \
  "$IMAGE" >/dev/null

say "waiting for health"
for _ in $(seq 1 30); do
  if curl -fsS "http://localhost:$PORT/health" >/dev/null 2>&1; then break; fi
  sleep 1
done
curl -fsS "http://localhost:$PORT/health" >/dev/null 2>&1 \
  || { warn "service did not become healthy — check: docker logs orivory-lite"; exit 1; }
say "healthy: http://localhost:$PORT"

if [[ "$WITH_CAPTURE" == 1 ]]; then
  say "registering agent client for auto-capture"
  # The API requires a verified human account; lite mode seeds one on first
  # boot with the credentials printed by the container log. We surface the
  # interactive registration instead of guessing secrets here.
  warn "open http://localhost:$PORT → sign up → Security page → register an agent"
  warn "then run: python3 scripts/openclaw_capture.py --watch ~/.openclaw/workspace \\"
  warn "    --url http://localhost:$PORT --token oa_... --interval 30"
fi

cat <<EOF

  Orivory (lite) is running.

    UI/API : http://localhost:$PORT
    Health : http://localhost:$PORT/health
    Data   : $DIR/data
    MCP    : http://localhost:$PORT/mcp  (agent tokens from the Security page)

  Next steps:
    1. Open http://localhost:$PORT and create your account.
    2. (Optional) Security page → register an agent → wire auto-capture:
       python3 scripts/openclaw_capture.py --watch ~/.openclaw/workspace \\
           --url http://localhost:$PORT --token oa_... --interval 30

  Manage: docker logs -f orivory-lite | docker restart orivory-lite |
          docker rm -f orivory-lite   (stop)

EOF
