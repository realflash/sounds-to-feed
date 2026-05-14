#!/usr/bin/env bash
# Standard Mobile Pipeline Script (v0.6)
# <!-- Standard Version: 0.6 -->

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Mobile Pipeline (v0.6)...${NC}"

# 0. Argument Parsing
DO_RELEASE_BUILD=false
EMULATOR_NAME="Medium_Phone_API_34"

# Allow overriding emulator name via environment or argument
if [[ "$*" == *"--emulator="* ]]; then
    EMULATOR_NAME=$(echo "$*" | grep -oP '(?<=--emulator=)[^ ]+')
fi

if [[ "$*" == *"--release"* ]]; then
    DO_RELEASE_BUILD=true
    echo -e "${YELLOW}📦 Release Mode Enabled (Multi-architecture build will run after tests)${NC}"
fi

echo -e "${BLUE}📱 Using Emulator: ${EMULATOR_NAME}${NC}"

# 1. Environment & Path Setup
export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$PATH:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$HOME/.maestro/bin"
export NO_PROXY="localhost,127.0.0.1,::1"
export no_proxy="localhost,127.0.0.1,::1"

# Ensure correct Java version if possible
if [ -d "/usr/lib/jvm/java-17-openjdk-amd64" ]; then
    export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
    echo -e "${BLUE}☕ Using JAVA_HOME=$JAVA_HOME${NC}"
fi

# 2. Service Management
METRO_PID=""

cleanup() {
    if [ -n "$METRO_PID" ]; then
        echo -e "\n${YELLOW}🛑 Stopping Metro Bundler (PID: $METRO_PID)...${NC}"
        kill -9 "$METRO_PID" 2>/dev/null
    fi
}
trap cleanup EXIT

setup_emulator() {
    echo -e "${YELLOW}📱 Checking Android Emulator ($EMULATOR_NAME)...${NC}"
    
    # 0. Fail early if specified AVD doesn't exist, but try auto-detection first
    if ! emulator -list-avds | grep -q "^${EMULATOR_NAME}$"; then
        echo -e "${YELLOW}⚠️  AVD '${EMULATOR_NAME}' not found. Searching for available AVDs...${NC}"
        local first_avd=$(emulator -list-avds | head -n 1)
        if [ -n "$first_avd" ]; then
            EMULATOR_NAME="$first_avd"
            echo -e "${GREEN}🔄 Falling back to available AVD: ${EMULATOR_NAME}${NC}"
        else
            echo -e "${RED}❌ No Android emulators (AVDs) found!${NC}"
            echo -e "${YELLOW}Please create one using Android Studio or 'avdmanager'.${NC}"
            return 1
        fi
    fi

    # 1. Clear ports that are known to cause issues
    echo -e "${YELLOW}Sweep for port conflicts (7001, 8081, 9001, 9002)...${NC}"
    fuser -k 8081/tcp > /dev/null 2>&1 || true
    fuser -k 7001/tcp > /dev/null 2>&1 || true
    fuser -k 9001/tcp > /dev/null 2>&1 || true
    fuser -k 9002/tcp > /dev/null 2>&1 || true
    sleep 1

    # 2. Check for running emulator and wait for it to be ready
    emu_serial=$(adb devices | grep "emulator" | head -n 1 | cut -f1)
    
    if [ -z "$emu_serial" ]; then
        echo -e "${YELLOW}🎬 Starting $EMULATOR_NAME...${NC}"
        emulator -avd "$EMULATOR_NAME" -memory 4096 -cores 4 -partition-size 4096 -no-snapshot-load > /dev/null 2>&1 &
        echo -e "${YELLOW}⏳ Waiting for ADB...${NC}"
        adb wait-for-device
        emu_serial=$(adb devices | grep "emulator" | head -n 1 | cut -f1)
    fi

    if [ -z "$emu_serial" ]; then
        echo -e "${RED}❌ Failed to find or start emulator.${NC}"
        return 1
    fi

    # Ensure device is not offline or unauthorized
    local state=$(adb -s "$emu_serial" get-state 2>/dev/null)
    if [ "$state" != "device" ]; then
        echo -e "${YELLOW}⏳ Waiting for device to be online (current: $state)...${NC}"
        adb -s "$emu_serial" wait-for-device
    fi

    echo -e "${YELLOW}⏳ Waiting for system boot...${NC}"
    local timeout=180
    local elapsed=0
    until [ "$(adb -s "$emu_serial" shell settings get global device_provisioned 2>/dev/null | tr -d '\r\n')" == "1" ]; do
        sleep 5
        elapsed=$((elapsed + 5))
        if [ $elapsed -gt $timeout ]; then
            echo -e "\n${RED}❌ Emulator failed to boot within ${timeout}s${NC}"
            return 1
        fi
        echo -n "."
    done
    
    # Extra stabilization for ADB bridge
    sleep 2
    echo -e "\n${GREEN}✅ Emulator Ready ($emu_serial).${NC}"
    return 0
}

setup_metro() {
    echo -e "${YELLOW}🌐 Starting Metro Bundler...${NC}"
    # EXPO_PACKAGER_HOSTNAME=10.0.2.2 tells the app to look for the host at 10.0.2.2 (standard Android alias)
    # We bind to all interfaces (0.0.0.0) so the emulator can reach the host regardless of bridge flaky-ness
    export EXPO_PACKAGER_HOSTNAME=10.0.2.2
    (cd src/mobile && CI=1 npx expo start --port 8081 --dev-client --host lan --clear > /tmp/metro.log 2>&1) &
    METRO_PID=$!
    
    echo -e "${YELLOW}⏳ Waiting for Metro (8081) to be healthy...${NC}"
    local timeout=60
    local elapsed=0
    until curl -s http://localhost:8081/status | grep -q "running"; do
        sleep 2
        elapsed=$((elapsed + 2))
        if [ $elapsed -gt $timeout ]; then
            echo -e "${RED}❌ Metro failed to start within ${timeout}s${NC}"
            return 1
        fi
    done
    
    # Warm up JS bundle
    echo -e "${YELLOW}⏳ Warming up JS bundle...${NC}"
    curl -s "http://localhost:8081/node_modules/expo-router/entry.bundle?platform=android&dev=true&minify=false" > /dev/null || true
    
    echo -e "${GREEN}✅ Metro Ready.${NC}"
    return 0
}

# Results tracking
declare -a STAGES
declare -a RESULTS

run_stage() {
    local stage_name="$1"
    local command="$2"
    
    echo -e "\n${YELLOW}🛠️  Stage: ${stage_name}...${NC}"
    
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

# 1. Formatting
run_stage "Formatting" "make fmt-mobile"
FMT_RESULT=$?

# 2. Linting
if [ $FMT_RESULT -eq 0 ]; then
    run_stage "Linting" "make lint-mobile"
    LINT_RESULT=$?
else
    STAGES+=("Linting")
    RESULTS+=("SKIPPED")
    LINT_RESULT=1
fi

# 3. Unit Testing
if [ $LINT_RESULT -eq 0 ]; then
    run_stage "Unit Testing" "make test-mobile"
    TEST_RESULT=$?
else
    STAGES+=("Unit Testing")
    RESULTS+=("SKIPPED")
    TEST_RESULT=1
fi

# 4. Building
if [ $TEST_RESULT -eq 0 ]; then
    run_stage "Building (Android Fast)" "(cd src/mobile/android && ./gradlew assembleDebug -PtargetArchs=x86_64)"
    BUILD_RESULT=$?
else
    STAGES+=("Building (Android Fast)")
    RESULTS+=("SKIPPED")
    BUILD_RESULT=1
fi

# 5. E2E Testing (Maestro)
if [ $BUILD_RESULT -eq 0 ]; then
    setup_emulator && setup_metro
    SETUP_RESULT=$?
    
    if [ $SETUP_RESULT -eq 0 ]; then
        echo -e "${YELLOW}📦 Refreshing app on $emu_serial...${NC}"
        adb -s "$emu_serial" shell pm clear com.anonymous.mobile > /dev/null 2>&1 || true
        adb -s "$emu_serial" uninstall com.anonymous.mobile > /dev/null 2>&1 || true
        
        if ! adb -s "$emu_serial" install src/mobile/android/app/build/outputs/apk/debug/app-debug.apk; then
            echo -e "${RED}❌ Failed to install APK.${NC}"
            exit 1
        fi
        
        echo -e "${YELLOW}🌉 Establishing ADB tunnels (8000, 8081)...${NC}"
        adb -s "$emu_serial" reverse --remove-all
        adb -s "$emu_serial" reverse tcp:8000 tcp:8000
        adb -s "$emu_serial" reverse tcp:8081 tcp:8081
        
        # Verify tunnel
        if ! adb -s "$emu_serial" reverse --list | grep -q "8081"; then
            echo -e "${RED}⚠️  Warning: Port 8081 tunnel not listed, app might fail to load script.${NC}"
        fi
        
        export MAESTRO_DRIVER_PORT=9001
        export MAESTRO_SERVER_PORT=9002
        export MAESTRO_SESSION_ID=$(date +%s)
        unset http_proxy https_proxy all_proxy
        
        echo -e "${YELLOW}🚀 Launching E2E Tests...${NC}"
        run_stage "E2E Testing (Maestro)" "maestro test src/mobile/.maestro/"
        E2E_RESULT=$?
    else
        echo -e "${RED}❌ E2E Setup failed.${NC}"
        STAGES+=("E2E Testing (Maestro)")
        RESULTS+=("FAIL")
        E2E_RESULT=1
    fi
else
    STAGES+=("E2E Testing (Maestro)")
    RESULTS+=("SKIPPED")
    E2E_RESULT=1
fi

# 6. Final Build
if [ $E2E_RESULT -eq 0 ] && [ "$DO_RELEASE_BUILD" = true ]; then
    run_stage "Full Production Build" "(cd src/mobile/android && ./gradlew assembleRelease)"
elif [ "$DO_RELEASE_BUILD" = true ]; then
    STAGES+=("Full Production Build")
    RESULTS+=("SKIPPED")
fi

cleanup

echo -e "\n${BLUE}📊 Summary:${NC}"
echo "----------------------"
PIPELINE_FAILED=0
for i in "${!STAGES[@]}"; do
    echo -e "${STAGES[$i]}: ${RESULTS[$i]}"
    if [ "${RESULTS[$i]}" != "PASS" ]; then PIPELINE_FAILED=1; fi
done
echo "----------------------"

exit $PIPELINE_FAILED
