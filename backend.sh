#!/bin/bash

# Backend management script for SAP BTP AI Assistant

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PATH=".venv/bin"
HOST="127.0.0.1"
PORT="8000"
LOG_FILE="/tmp/backend_sap_agent.log"
PID_FILE="/tmp/backend_sap_agent.pid"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "❌ Backend is already running (PID: $PID)"
            echo "   Use './backend.sh stop' to stop it first"
            exit 1
        else
            rm -f "$PID_FILE"
        fi
    fi

    echo "🚀 Starting backend..."

    if [ ! -d "$VENV_PATH" ]; then
        echo "❌ Virtual environment not found at $VENV_PATH"
        echo "   Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi

    # Start uvicorn in background
    AGENT_CALLABLE=backend.agent:stream_agent \
        "$VENV_PATH/uvicorn" backend.main:app \
        --host "$HOST" \
        --port "$PORT" \
        > "$LOG_FILE" 2>&1 &

    echo $! > "$PID_FILE"

    # Wait a moment and check if it started successfully
    sleep 2

    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "✅ Backend started successfully!"
        echo "   PID: $(cat "$PID_FILE")"
        echo "   URL: http://$HOST:$PORT"
        echo "   Log: $LOG_FILE"
        echo ""
        echo "   Tail logs: tail -f $LOG_FILE"
    else
        echo "❌ Backend failed to start. Check logs:"
        echo "   cat $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  No PID file found. Attempting to kill by port..."
        lsof -ti:$PORT | xargs kill -9 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ Killed process on port $PORT"
        else
            echo "ℹ️  No backend process found"
        fi
        return
    fi

    PID=$(cat "$PID_FILE")

    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 Stopping backend (PID: $PID)..."
        kill $PID 2>/dev/null

        # Wait for graceful shutdown
        for i in {1..5}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "   Force killing..."
            kill -9 $PID 2>/dev/null
        fi

        rm -f "$PID_FILE"
        echo "✅ Backend stopped"
    else
        echo "ℹ️  Backend not running (stale PID file)"
        rm -f "$PID_FILE"
    fi
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ Backend is running"
            echo "   PID: $PID"
            echo "   URL: http://$HOST:$PORT"
            echo "   Log: $LOG_FILE"
            echo ""
            echo "Recent logs:"
            tail -10 "$LOG_FILE"
        else
            echo "❌ Backend not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        echo "❌ Backend is not running"
    fi
}

restart() {
    echo "🔄 Restarting backend..."
    stop
    sleep 1
    start
}

logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "❌ Log file not found: $LOG_FILE"
        exit 1
    fi

    if [ "$1" = "-f" ] || [ "$1" = "--follow" ]; then
        echo "📋 Following logs (Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
    else
        echo "📋 Recent logs:"
        tail -50 "$LOG_FILE"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    *)
        echo "SAP BTP AI Assistant - Backend Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start     Start the backend server"
        echo "  stop      Stop the backend server"
        echo "  restart   Restart the backend server"
        echo "  status    Check backend status"
        echo "  logs      Show recent logs"
        echo "  logs -f   Follow logs in real-time"
        echo ""
        exit 1
        ;;
esac
