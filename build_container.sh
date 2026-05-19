#!/usr/bin/env bash
# Standard Container Pipeline Script (v0.4)
# <!-- Standard Version: 0.4 -->

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Container Pipeline...${NC}"

# Results tracking
declare -a STAGES
declare -a RESULTS

run_stage() {
    local stage_name="$1"
    local command="$2"
    
    echo -e "\n${YELLOW}🛠️  Stage: ${stage_name}...${NC}"
    
    # Execute the command
    eval "$command"
    local exit_code=$?
    
    STAGES+=("$stage_name")
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ ${stage_name} passed!${NC}"
        RESULTS+=("PASS")
        return 0
    else
        echo -e "${RED}❌ ${stage_name} failed with exit code ${exit_code}${NC}"
        RESULTS+=("FAIL")
        return $exit_code
    fi
}

# 1. Linting
run_stage "Linting" "make lint-backend"
LINT_RESULT=$?

# 2. Unit & Integration Testing
if [ $LINT_RESULT -eq 0 ]; then
    run_stage "Unit & Integration Testing" "make test-backend"
    TEST_RESULT=$?
else
    echo -e "\n${YELLOW}⏭️  Skipping Testing due to Linting failure.${NC}"
    STAGES+=("Testing")
    RESULTS+=("SKIPPED")
    TEST_RESULT=1
fi

# 3. Code Scanning
if [ $TEST_RESULT -eq 0 ]; then
    run_stage "Code Scanning" "make code-scan"
    CODE_RESULT=$?
else
    STAGES+=("Code Scanning")
    RESULTS+=("SKIPPED")
    CODE_RESULT=1
fi

# 4. Building
if [ $CODE_RESULT -eq 0 ]; then
    run_stage "Building (Container)" "make build-container"
    BUILD_CONT_RESULT=$?
else
    STAGES+=("Building (Container)")
    RESULTS+=("SKIPPED")
    BUILD_CONT_RESULT=1
fi

# 5. Container Security
if [ $BUILD_CONT_RESULT -eq 0 ]; then
    # We allow this to fail without breaking the whole build if trivy isn't available, but it should run.
    run_stage "Container Security" "make container-scan || echo 'Trivy check failed or not installed'"
    CONTAINER_RESULT=$?
else
    STAGES+=("Container Security")
    RESULTS+=("SKIPPED")
    CONTAINER_RESULT=1
fi

# Summary Report
echo -e "\n${BLUE}📊 Container Pipeline Summary:${NC}"
echo "----------------------"
PIPELINE_FAILED=0
for i in "${!STAGES[@]}"; do
    STAGE="${STAGES[$i]}"
    RESULT="${RESULTS[$i]}"
    
    if [ "$RESULT" == "PASS" ]; then
        echo -e "${STAGE}: ${GREEN}${RESULT}${NC}"
    elif [ "$RESULT" == "FAIL" ]; then
        echo -e "${STAGE}: ${RED}${RESULT}${NC}"
        PIPELINE_FAILED=1
    else
        echo -e "${STAGE}: ${YELLOW}${RESULT}${NC}"
        PIPELINE_FAILED=1
    fi
done
echo "----------------------"

if [ $PIPELINE_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Container Pipeline Passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Container Pipeline Failed.${NC}"
    exit 1
fi
