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

# 0. Library Setup
run_stage "Library Setup" "make build-libs"
LIBS_RESULT=$?

# 1. Dependencies
if [ $LIBS_RESULT -eq 0 ]; then
    run_stage "Dependencies" "make install-e2e"
    DEPENDENCIES_RESULT=$?
else
    echo -e "\n${YELLOW}⏭️  Skipping Dependencies due to Library failure.${NC}"
    STAGES+=("Dependencies")
    RESULTS+=("SKIPPED")
    DEPENDENCIES_RESULT=1
fi

# 2. Linting
if [ $DEPENDENCIES_RESULT -eq 0 ]; then
    run_stage "Linting (Web)" "make lint-web"
    LINT_WEB_RESULT=$?
else
    echo -e "\n${YELLOW}⏭️  Skipping Linting due to Dependency failure.${NC}"
    STAGES+=("Linting (Web)")
    RESULTS+=("SKIPPED")
    LINT_WEB_RESULT=1
fi

# 2. Unit & Integration Testing
if [ $LINT_WEB_RESULT -eq 0 ]; then
    run_stage "Unit & Integration Testing (Web)" "make test-web"
    TEST_WEB_RESULT=$?
else
    echo -e "\n${YELLOW}⏭️  Skipping Testing due to Linting failure.${NC}"
    STAGES+=("Testing")
    RESULTS+=("SKIPPED")
    TEST_WEB_RESULT=1
fi

# 3. Code Scanning
if [ $TEST_WEB_RESULT -eq 0 ]; then
    run_stage "Code Scanning" "make code-scan"
    CODE_RESULT=$?
else
    STAGES+=("Code Scanning")
    RESULTS+=("SKIPPED")
    CODE_RESULT=1
fi

# 4. E2E Testing (Mocked)
if [ $CODE_RESULT -eq 0 ]; then
    run_stage "E2E Testing (Mocked)" "make test-e2e"
    E2E_MOCK_RESULT=$?
else
    STAGES+=("E2E Testing (Mocked)")
    RESULTS+=("SKIPPED")
    E2E_MOCK_RESULT=1
fi

# 5. E2E Testing (System)
if [ $E2E_MOCK_RESULT -eq 0 ]; then
    run_stage "E2E Testing (System)" "make test-e2e-system"
    E2E_SYS_RESULT=$?
else
    STAGES+=("E2E Testing (System)")
    RESULTS+=("SKIPPED")
    E2E_SYS_RESULT=1
fi

# 6. Building
if [ $E2E_SYS_RESULT -eq 0 ]; then
    run_stage "Building (Container)" "make build-container"
    BUILD_CONT_RESULT=$?
else
    STAGES+=("Building (Container)")
    RESULTS+=("SKIPPED")
    BUILD_CONT_RESULT=1
fi

# 7. Container Security
if [ $BUILD_CONT_RESULT -eq 0 ]; then
    run_stage "Container Security" "make container-scan"
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
