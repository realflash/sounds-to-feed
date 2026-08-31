#!/usr/bin/env bash
# Standard Local Pipeline Script (v0.4)
# <!-- Standard Version: 0.4 -->

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BUILD_ID=$(make info | grep "Build ID:" | cut -d' ' -f3)
echo -e "${BLUE}🚀 Starting Master Pipeline (Build: ${BUILD_ID})...${NC}"

echo -e "\n${YELLOW}🏗️  Running Container Pipeline...${NC}"
./build_container.sh
PIPELINE_FAILED=$?

if [ $PIPELINE_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ Master Pipeline Passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Master Pipeline Failed.${NC}"
    exit 1
fi
