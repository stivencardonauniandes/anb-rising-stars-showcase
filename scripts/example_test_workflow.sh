#!/bin/bash
#
# Example testing workflow for SQS Queue performance
# This script demonstrates a complete testing sequence based on the capacity planning test plan
#

set -e

echo "🎯 SQS Queue Performance Testing Workflow"
echo "=============================================="
echo ""

# Configuration
AWS_REGION="us-east-1"
SQS_QUEUE_URL="https://sqs.us-east-1.amazonaws.com/254740242224/anb-rising-stars"

# Validate SQS_QUEUE_URL is set
if [ -z "$SQS_QUEUE_URL" ]; then
    echo "❌ Error: SQS_QUEUE_URL is not set"
    echo "Please set the SQS_QUEUE_URL variable in this script"
    exit 1
fi

# Test task configuration (optional - leave empty for auto-generated values)
VIDEO_ID="dad46663-441a-472f-8c4d-364783d83ed1"  # e.g., "753f41bb-e995-4236-ad2d-3c06597f976b" or leave empty for random UUID
SOURCE_PATH="/raw/550e8400-e29b-41d4-a716-446655440004.mp4"  # e.g., "/raw/video.mp4" or leave empty for auto-generated path

# Test configuration
SATURATION_RATE=10  # Tasks per second for saturation test
SATURATION_DURATION=300  # 5 minutes
SATURATION_TARGET_SIZE=600  # Max queue size for saturation test

STEADY_STATE_TARGET=200  # Target queue size to maintain
STEADY_STATE_RATE=10  # Base rate for steady state
STEADY_STATE_DURATION=300  # 5 minutes
STEADY_STATE_TOLERANCE=0.1  # 10% tolerance

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check initial status
echo -e "${GREEN}Step 1: Checking initial queue status${NC}"
python3 sqs_queue_test.py status --region $AWS_REGION --queue-url "$SQS_QUEUE_URL"
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 2: Add a single task
echo -e "${GREEN}Step 2: Adding a single test task${NC}"
echo -e "${YELLOW}This tests basic connectivity and worker processing${NC}"

# Build the add-task command with optional parameters
ADD_TASK_CMD="python3 sqs_queue_test.py add-task --region $AWS_REGION --queue-url \"$SQS_QUEUE_URL\""
if [ -n "$VIDEO_ID" ]; then
    ADD_TASK_CMD="$ADD_TASK_CMD --video-id $VIDEO_ID"
fi
if [ -n "$SOURCE_PATH" ]; then
    ADD_TASK_CMD="$ADD_TASK_CMD --source-path $SOURCE_PATH"
fi

# Execute the command
eval $ADD_TASK_CMD
echo ""
echo -e "${YELLOW}Waiting 10 seconds to see if worker processes the task...${NC}"
sleep 10
python3 sqs_queue_test.py status --region $AWS_REGION --queue-url "$SQS_QUEUE_URL"
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 3: Clear the queue before testing
echo -e "${GREEN}Step 3: Clearing queue before performance tests${NC}"
echo -e "${YELLOW}This ensures we start from a clean state${NC}"
python3 sqs_queue_test.py clear --region $AWS_REGION --queue-url "$SQS_QUEUE_URL"
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 4: Run saturation test
echo -e "${GREEN}Step 4: Running Saturation Test${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Objective: Find the breaking point of the system${NC}"
echo ""
echo -e "Configuration:"
echo -e "  - Rate: ${SATURATION_RATE} tasks/second"
echo -e "  - Duration: ${SATURATION_DURATION} seconds (~$(($SATURATION_DURATION / 60)) minutes)"
echo -e "  - Target size: ${SATURATION_TARGET_SIZE} tasks"
echo -e "  - Batch size: 10 tasks per batch"
echo ""
echo -e "${YELLOW}Monitor your metrics dashboard during this test${NC}"
echo -e "${YELLOW}Expected behaviors:${NC}"
echo -e "  ✓ Queue grows if workers can't keep up"
echo -e "  ✓ Throughput plateaus at system capacity"
echo -e "  ✓ Service time may increase under load"
echo ""
read -p "Press Enter to start saturation test..."
echo ""

# Build the saturation command with optional parameters
SATURATION_CMD="python3 sqs_queue_test.py saturation --region $AWS_REGION --queue-url \"$SQS_QUEUE_URL\" --rate $SATURATION_RATE --duration $SATURATION_DURATION --target-size $SATURATION_TARGET_SIZE --batch-size 10"
if [ -n "$VIDEO_ID" ]; then
    SATURATION_CMD="$SATURATION_CMD --video-id $VIDEO_ID"
fi
if [ -n "$SOURCE_PATH" ]; then
    SATURATION_CMD="$SATURATION_CMD --source-path $SOURCE_PATH"
fi

# Execute the command
eval $SATURATION_CMD
echo ""

# Step 5: Analyze saturation results
echo -e "${GREEN}Step 5: Analyzing saturation test results${NC}"
python3 sqs_queue_test.py status --region $AWS_REGION --queue-url "$SQS_QUEUE_URL"
echo ""
echo -e "${YELLOW}Saturation Test Analysis:${NC}"
echo -e "Review your metrics to determine:"
echo -e "  - Maximum throughput achieved (videos/min)"
echo -e "  - Queue size at saturation point"
echo -e "  - Average service time under load"
echo -e "  - p95 latency"
echo -e "  - Error rate (should be < 5%)"
echo ""
echo -e "${YELLOW}Letting workers process for 30 seconds...${NC}"
sleep 30
python3 sqs_queue_test.py status --region $AWS_REGION --queue-url "$SQS_QUEUE_URL"
echo ""
read -p "Press Enter to continue to steady-state test..."
echo ""

# Step 6: Clear queue before steady-state test
echo -e "${GREEN}Step 6: Clearing queue before steady-state test${NC}"
python3 sqs_queue_test.py clear --region $AWS_REGION --queue-url "$SQS_QUEUE_URL"
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 7: Run steady-state test
echo -e "${GREEN}Step 7: Running Steady-State Test${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Objective: Validate stability under constant load${NC}"
echo ""
echo -e "Configuration:"
echo -e "  - Target queue size: ${STEADY_STATE_TARGET} tasks"
echo -e "  - Base rate: ${STEADY_STATE_RATE} tasks/second"
echo -e "  - Duration: ${STEADY_STATE_DURATION} seconds (~$(($STEADY_STATE_DURATION / 60)) minutes)"
echo -e "  - Tolerance: ${STEADY_STATE_TOLERANCE} ($(echo "$STEADY_STATE_TOLERANCE * 100" | bc)%)"
echo -e "  - Acceptable range: $(echo "$STEADY_STATE_TARGET * (1 - $STEADY_STATE_TOLERANCE)" | bc) - $(echo "$STEADY_STATE_TARGET * (1 + $STEADY_STATE_TOLERANCE)" | bc) tasks"
echo ""
echo -e "${YELLOW}Monitor your metrics dashboard during this test${NC}"
echo -e "${YELLOW}Success criteria:${NC}"
echo -e "  ✓ Queue size stays within tolerance range"
echo -e "  ✓ Queue trend ≈ 0 (between -0.1 and 0.1 tasks/min)"
echo -e "  ✓ Success rate > 99%"
echo -e "  ✓ Throughput deviation < 10%"
echo ""
read -p "Press Enter to start steady-state test..."
echo ""

# Build the steady-state command with optional parameters
STEADY_STATE_CMD="python3 sqs_queue_test.py steady-state --region $AWS_REGION --queue-url \"$SQS_QUEUE_URL\" --target $STEADY_STATE_TARGET --rate $STEADY_STATE_RATE --duration $STEADY_STATE_DURATION --tolerance $STEADY_STATE_TOLERANCE"
if [ -n "$VIDEO_ID" ]; then
    STEADY_STATE_CMD="$STEADY_STATE_CMD --video-id $VIDEO_ID"
fi
if [ -n "$SOURCE_PATH" ]; then
    STEADY_STATE_CMD="$STEADY_STATE_CMD --source-path $SOURCE_PATH"
fi

# Execute the command
eval $STEADY_STATE_CMD
echo ""

# Step 8: Final analysis
echo -e "${GREEN}Step 8: Final Analysis and Results${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
python3 sqs_queue_test.py status --region $AWS_REGION --queue-url "$SQS_QUEUE_URL"
echo ""
echo -e "${YELLOW}Steady-State Test Analysis:${NC}"
echo -e "Review your metrics to determine:"
echo -e "  - Average throughput (videos/min)"
echo -e "  - Queue stability (std deviation)"
echo -e "  - Queue trend (tasks/min)"
echo -e "  - Average service time"
echo -e "  - Success rate (%)"
echo -e "  - System stability verdict"
echo ""

# Print summary table
echo -e "${GREEN}Test Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "Configuration:"
echo -e "  AWS Region: $AWS_REGION"
echo -e "  Queue URL: $SQS_QUEUE_URL"
echo ""
echo -e "Saturation Test:"
echo -e "  Rate: $SATURATION_RATE tasks/sec"
echo -e "  Duration: $(($SATURATION_DURATION / 60)) minutes"
echo -e "  Target: $SATURATION_TARGET_SIZE tasks"
echo ""
echo -e "Steady-State Test:"
echo -e "  Target: $STEADY_STATE_TARGET tasks"
echo -e "  Rate: $STEADY_STATE_RATE tasks/sec"
echo -e "  Duration: $(($STEADY_STATE_DURATION / 60)) minutes"
echo -e "  Tolerance: $(echo "$STEADY_STATE_TOLERANCE * 100" | bc)%"
echo ""

echo "=============================================="
echo "✅ Testing workflow complete!"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Review metrics in your monitoring dashboard"
echo "2. Calculate key performance indicators:"
echo "   - Throughput (X): videos/min"
echo "   - Service time (S): seconds/video"
echo "   - Queue trend: tasks/min"
echo "   - Success rate: %"
echo "3. Compare results against success criteria:"
echo "   - Saturation: Queue manageable, errors < 5%"
echo "   - Steady-State: Queue stable, trend ≈ 0"
echo "4. Document findings for capacity planning"
echo ""
