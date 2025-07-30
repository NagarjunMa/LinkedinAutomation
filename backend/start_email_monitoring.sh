#!/bin/bash

# Start Email Monitoring System
echo "🚀 Starting Email Monitoring System..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   brew services start redis"
    echo "   or"
    echo "   redis-server"
    exit 1
fi

echo "✅ Redis is running"

# Start Celery Beat Scheduler (for periodic tasks)
echo "📅 Starting Celery Beat Scheduler..."
celery -A app.core.celery_app beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler &
BEAT_PID=$!

# Start Celery Worker (for processing tasks)
echo "👷 Starting Celery Worker..."
celery -A app.core.celery_app worker --loglevel=info --concurrency=2 &
WORKER_PID=$!

echo "✅ Email monitoring system started!"
echo "   - Beat Scheduler PID: $BEAT_PID"
echo "   - Worker PID: $WORKER_PID"
echo ""
echo "📊 Monitoring will:"
echo "   - Check for new emails every 5 minutes"
echo "   - Process emails automatically"
echo "   - Update job statuses in real-time"
echo "   - Refresh Gmail tokens every hour"
echo ""
echo "🔍 To check monitoring status:"
echo "   curl http://localhost:8000/api/v1/email-agent/monitoring-status"
echo ""
echo "🛑 To stop monitoring:"
echo "   kill $BEAT_PID $WORKER_PID"
echo ""
echo "📝 Logs will appear below..."

# Wait for user to stop
wait 