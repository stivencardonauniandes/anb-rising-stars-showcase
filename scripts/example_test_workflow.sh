#!/bin/bash
#
# Example testing workflow for Redis Stream performance
# This script demonstrates a complete testing sequence
#

set -e

echo "🎯 Redis Stream Performance Testing Workflow"
echo "=============================================="
echo ""

# Configuration
REDIS_HOST="54.162.162.14"
REDIS_PORT="6379"

# Test task configuration (optional - leave empty for auto-generated values)
VIDEO_ID="753f41bb-e995-4236-ad2d-3c06597f976b"  # e.g., "test-video-12345" or leave empty for random UUID
SOURCE_PATH="/raw/x161d29df1-aef2-45d8-bddc-deff9716e1f1.mp4"  # e.g., "test/videos/sample.mp4" or leave empty for auto-generated path

# Saturation test mode: set to "manual" to use manual stop (press Enter), or "auto" for time/size limits
SATURATION_MODE="manual"  # Options: "manual" or "auto"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check initial status
echo -e "${GREEN}Step 1: Checking initial stream status${NC}"
python3 redis_stream_test.py status --host $REDIS_HOST --port $REDIS_PORT
python3 redis_stream_test.py clear --host $REDIS_HOST --port $REDIS_PORT
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 2: Add a single task
echo -e "${GREEN}Step 2: Adding a single test task${NC}"
echo -e "${YELLOW}This tests basic connectivity and worker processing${NC}"

# Build the add-task command with optional parameters
ADD_TASK_CMD="python3 redis_stream_test.py add-task --host $REDIS_HOST --port $REDIS_PORT"
if [ -n "$VIDEO_ID" ]; then
    ADD_TASK_CMD="$ADD_TASK_CMD --video-id $VIDEO_ID"
fi
if [ -n "$SOURCE_PATH" ]; then
    ADD_TASK_CMD="$ADD_TASK_CMD --source-path $SOURCE_PATH"
fi

# Execute the command
eval $ADD_TASK_CMD
echo ""
echo -e "${YELLOW}Waiting 5 seconds to see if worker processes the task...${NC}"
sleep 5
python3 redis_stream_test.py status --host $REDIS_HOST --port $REDIS_PORT
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 3: Clear the stream
echo -e "${GREEN}Step 3: Clearing stream (if needed)${NC}"
echo -e "${YELLOW}This will prompt for confirmation${NC}"
python3 redis_stream_test.py clear --host $REDIS_HOST --port $REDIS_PORT
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 4: Run saturation test
echo -e "${GREEN}Step 4: Running saturation test${NC}"

# Build the saturation command with optional parameters
if [ "$SATURATION_MODE" = "manual" ]; then
    echo -e "${YELLOW}Mode: Manual stop - press ENTER to stop adding tasks${NC}"
    echo -e "${YELLOW}This will add tasks as fast as possible (UNLIMITED rate) to saturate the system${NC}"
    echo -e "${YELLOW}Monitor Grafana at http://localhost:3000 during this test${NC}"
    SATURATION_CMD="python3 redis_stream_test.py saturation --host $REDIS_HOST --port $REDIS_PORT --rate 0 --batch-size 10 --manual-stop"
else
    echo -e "${YELLOW}Mode: Automatic (60s, unlimited rate, max 100 tasks)${NC}"
    echo -e "${YELLOW}This will add tasks as fast as possible to reach target size${NC}"
    echo -e "${YELLOW}Monitor Grafana at http://localhost:3000 during this test${NC}"
    SATURATION_CMD="python3 redis_stream_test.py saturation --host $REDIS_HOST --port $REDIS_PORT --rate 0 --batch-size 10 --duration 60 --target-size 600"
fi

if [ -n "$VIDEO_ID" ]; then
    SATURATION_CMD="$SATURATION_CMD --video-id $VIDEO_ID"
fi
if [ -n "$SOURCE_PATH" ]; then
    SATURATION_CMD="$SATURATION_CMD --source-path $SOURCE_PATH"
fi

# Execute the command
eval $SATURATION_CMD
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 5: Check status after saturation
echo -e "${GREEN}Step 5: Checking status after saturation test${NC}"
python3 redis_stream_test.py status --host $REDIS_HOST --port $REDIS_PORT
echo ""
echo -e "${YELLOW}Wait a moment for workers to process some tasks...${NC}"
sleep 10
echo ""

# Step 3: Clear the stream
echo -e "${GREEN}Step 3: Clearing stream (if needed)${NC}"
echo -e "${YELLOW}This will prompt for confirmation${NC}"
python3 redis_stream_test.py clear --host $REDIS_HOST --port $REDIS_PORT
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 6: Run steady-state test
echo -e "${GREEN}Step 6: Running steady-state test (300s, maintain 1000 tasks)${NC}"
echo -e "${YELLOW}This will demonstrate balanced load${NC}"

# Build the steady-state command with optional parameters
STEADY_STATE_CMD="python3 redis_stream_test.py steady-state --host $REDIS_HOST --port $REDIS_PORT --target 200 --rate 2 --duration 100 --tolerance 0.1"
if [ -n "$VIDEO_ID" ]; then
    STEADY_STATE_CMD="$STEADY_STATE_CMD --video-id $VIDEO_ID"
fi
if [ -n "$SOURCE_PATH" ]; then
    STEADY_STATE_CMD="$STEADY_STATE_CMD --source-path $SOURCE_PATH"
fi

# Execute the command
eval $STEADY_STATE_CMD
echo ""

# Step 7: Final status
echo -e "${GREEN}Step 7: Final status check${NC}"
python3 redis_stream_test.py status --host $REDIS_HOST --port $REDIS_PORT
echo ""

echo "=============================================="
echo "✅ Testing workflow complete!"
echo ""
echo "📊 Review the results:"
echo "   - Grafana dashboards: http://localhost:3000"
echo "   - Redis Insight: http://localhost:5540"
echo ""
