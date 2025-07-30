#!/bin/bash
# Celery Startup Script for RSS Feed Scheduler

echo "🚀 Starting Celery Services for RSS Feed Automation"
echo "================================================="

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis not running. Starting Redis..."
    
    # Try to start Redis (macOS)
    if command -v brew > /dev/null; then
        brew services start redis
        sleep 2
    else
        echo "💡 Please start Redis manually: redis-server"
        exit 1
    fi
fi

echo "✅ Redis is running"

# Set working directory
cd "$(dirname "$0")"

# Kill any existing Celery processes
echo "🧹 Cleaning up existing Celery processes..."
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true
sleep 2

# Start Celery worker in background
echo "🟡 Starting Celery Worker..."
nohup celery -A app.core.celery_app worker --loglevel=info --concurrency=2 > logs/celery_worker.log 2>&1 &
WORKER_PID=$!

# Give worker time to start
sleep 3

# Start Celery beat in background  
echo "🟢 Starting Celery Beat (Scheduler)..."
nohup celery -A app.core.celery_app beat --loglevel=info > logs/celery_beat.log 2>&1 &
BEAT_PID=$!

# Give beat time to start
sleep 2

echo "✅ Celery services started!"
echo "   Worker PID: $WORKER_PID"
echo "   Beat PID: $BEAT_PID"
echo "   Logs: logs/celery_worker.log & logs/celery_beat.log"

# Verify services are running
sleep 1
if ps -p $WORKER_PID > /dev/null; then
    echo "✅ Celery Worker: Running"
else
    echo "❌ Celery Worker: Failed to start"
fi

if ps -p $BEAT_PID > /dev/null; then
    echo "✅ Celery Beat: Running"
else
    echo "❌ Celery Beat: Failed to start"
fi

echo ""
echo "📅 RSS Feed Schedule:"
echo "   - Refresh every 60 minutes"
echo "   - Cleanup old jobs daily"
echo "   - AI job scoring after each refresh"
echo ""
echo "🔍 Monitor with:"
echo "   tail -f logs/celery_worker.log"
echo "   tail -f logs/celery_beat.log"
echo ""
echo "🛑 Stop with:"
echo "   pkill -f \"celery.*worker\""
echo "   pkill -f \"celery.*beat\"" 