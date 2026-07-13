#!/usr/bin/env bash
# Start MCP server + Inspector for turtleatlas-w40k-11e
# Usage: ./start-mcp.sh [port]
# Kill with: kill $(cat /tmp/mcp-server.pid /tmp/mcp-inspector.pid 2>/dev/null)

set -e

PORT="${1:-3456}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$SCRIPT_DIR/mcp-server"
LOG_DIR="/tmp"

cleanup() {
    echo ""
    echo "Shutting down..."
    [ -f /tmp/mcp-server.pid ] && kill "$(cat /tmp/mcp-server.pid)" 2>/dev/null && rm /tmp/mcp-server.pid
    [ -f /tmp/mcp-inspector.pid ] && kill "$(cat /tmp/mcp-inspector.pid)" 2>/dev/null && rm /tmp/mcp-inspector.pid
    echo "Done."
}
trap cleanup EXIT INT TERM

# Kill any existing instances
[ -f /tmp/mcp-server.pid ] && kill "$(cat /tmp/mcp-server.pid)" 2>/dev/null || true
[ -f /tmp/mcp-inspector.pid ] && kill "$(cat /tmp/mcp-inspector.pid)" 2>/dev/null || true
sleep 1

# 1) Start MCP server
echo "Starting MCP server on port $PORT..."
cd "$SERVER_DIR"
node index.js --port="$PORT" > "$LOG_DIR/mcp-server.log" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > /tmp/mcp-server.pid

# Wait for server to be healthy
for i in $(seq 1 10); do
    if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
        echo "  Server OK (PID $SERVER_PID)"
        break
    fi
    sleep 1
done

# 2) Start MCP Inspector
echo "Starting MCP Inspector..."
npx @modelcontextprotocol/inspector \
    --transport http \
    --server-url "http://localhost:$PORT/mcp" \
    > "$LOG_DIR/mcp-inspector.log" 2>&1 &
INSPECTOR_PID=$!
echo $INSPECTOR_PID > /tmp/mcp-inspector.pid

# Wait for inspector URL
sleep 3
INSPECTOR_URL=$(grep -oP 'http://localhost:\d+/\?MCP_PROXY_AUTH_TOKEN=\S+' "$LOG_DIR/mcp-inspector.log" | head -1)

echo ""
echo "============================================"
echo "  MCP Server:   http://localhost:$PORT/mcp"
echo "  Inspector:    ${INSPECTOR_URL:-check /tmp/mcp-inspector.log}"
echo "  Server log:   $LOG_DIR/mcp-server.log"
echo "  Inspector log:$LOG_DIR/mcp-inspector.log"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop both."

# Wait forever
wait
