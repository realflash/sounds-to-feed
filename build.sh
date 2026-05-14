#!/usr/bin/env bash
# Standard Local Pipeline Script (v0.4)
# <!-- Standard Version: 0.4 -->

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Scope filtering
SCOPE=${1:-all} # Supported: all, container, mobile

BUILD_ID=$(make info | grep "Build ID:" | cut -d' ' -f3)
echo -e "${BLUE}🚀 Starting Master Pipeline (Build: ${BUILD_ID}, Scope: ${SCOPE})...${NC}"

# Results tracking
PIPELINE_FAILED=0

if [ "$SCOPE" == "all" ] || [ "$SCOPE" == "container" ]; then
    echo -e "\n${YELLOW}🏗️  Running Container Pipeline...${NC}"
    ./build-container.sh
    if [ $? -ne 0 ]; then PIPELINE_FAILED=1; fi
fi

if [ "$SCOPE" == "all" ] || [ "$SCOPE" == "mobile" ]; then
    echo -e "\n${YELLOW}📱 Running Mobile Pipeline...${NC}"
    ./build-mobile.sh
    if [ $? -ne 0 ]; then PIPELINE_FAILED=1; fi
fi

if [ $PIPELINE_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ Master Pipeline Passed (Scope: ${SCOPE})!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Master Pipeline Failed (Scope: ${SCOPE}).${NC}"
    exit 1
fi
