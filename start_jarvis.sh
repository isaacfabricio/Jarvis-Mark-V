#!/usr/bin/env bash
set -u

APP_DIR="/workspaces/Jarvis-Mark-V"
LOG_FILE="/tmp/jarvis.log"
PID_FILE="/tmp/jarvis.pid"
PORT=8000

mkdir -p "$(dirname "$LOG_FILE")"

start_app() {
  cd "$APP_DIR" || exit 1
  if curl -fsS "http://127.0.0.1:$PORT" >/dev/null 2>&1; then
    echo "J.A.R.V.I.S. já está respondendo na porta $PORT."
    return 0
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] iniciando J.A.R.V.I.S..." >> "$LOG_FILE"
  nohup python cerebro_api.py >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  echo "J.A.R.V.I.S. iniciado com PID $(cat "$PID_FILE")"
  sleep 2
}

stop_app() {
  if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE" 2>/dev/null)"
    if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
      kill "$PID" 2>/dev/null || true
      echo "J.A.R.V.I.S. parado (PID $PID)."
    fi
  fi
  rm -f "$PID_FILE"
}

status_app() {
  if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE" 2>/dev/null)"
    if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
      echo "J.A.R.V.I.S. ativo (PID $PID)"
      return 0
    fi
  fi

  if curl -fsS "http://127.0.0.1:$PORT" >/dev/null 2>&1; then
    echo "J.A.R.V.I.S. respondendo na porta $PORT."
    return 0
  fi

  echo "J.A.R.V.I.S. parado."
  return 1
}

case "${1:-start}" in
  start)
    start_app
    while true; do
      if ! curl -fsS "http://127.0.0.1:$PORT" >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] processo caiu; reiniciando..." >> "$LOG_FILE"
        start_app
      fi
      sleep 5
    done
    ;;
  stop)
    stop_app
    ;;
  status)
    status_app
    ;;
  *)
    echo "Uso: $0 {start|stop|status}"
    exit 1
    ;;
esac
