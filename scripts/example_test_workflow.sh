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
REDIS_HOST="localhost"
REDIS_PORT="6379"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check initial status
echo -e "${GREEN}Step 1: Checking initial stream status${NC}"
python3 redis_stream_test.py status --host $REDIS_HOST --port $REDIS_PORT
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 2: Clear the stream
echo -e "${GREEN}Step 2: Clearing stream (if needed)${NC}"
echo -e "${YELLOW}This will prompt for confirmation${NC}"
python3 redis_stream_test.py clear --host $REDIS_HOST --port $REDIS_PORT
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 3: Run saturation test
echo -e "${GREEN}Step 3: Running saturation test (60s, 100 tasks/sec)${NC}"
echo -e "${YELLOW}Monitor Grafana at http://localhost:3000 during this test${NC}"
python3 redis_stream_test.py saturation \
    --host $REDIS_HOST \
    --port $REDIS_PORT \
    --rate 100 \
    --duration 60 \
    --target-size 10000
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 4: Check status after saturation
echo -e "${GREEN}Step 4: Checking status after saturation test${NC}"
python3 redis_stream_test.py status --host $REDIS_HOST --port $REDIS_PORT
echo ""
echo -e "${YELLOW}Wait a moment for workers to process some tasks...${NC}"
sleep 10
echo ""

# Step 5: Run steady-state test
echo -e "${GREEN}Step 5: Running steady-state test (300s, maintain 1000 tasks)${NC}"
echo -e "${YELLOW}This will demonstrate balanced load${NC}"
python3 redis_stream_test.py steady-state \
    --host $REDIS_HOST \
    --port $REDIS_PORT \
    --target 1000 \
    --rate 50 \
    --duration 300 \
    --tolerance 0.1
echo ""

# Step 6: Final status
echo -e "${GREEN}Step 6: Final status check${NC}"
python3 redis_stream_test.py status --host $REDIS_HOST --port $REDIS_PORT
echo ""

echo "=============================================="
echo "✅ Testing workflow complete!"
echo ""
echo "📊 Review the results:"
echo "   - Grafana dashboards: http://localhost:3000"
echo "   - Redis Insight: http://localhost:5540"
echo ""
