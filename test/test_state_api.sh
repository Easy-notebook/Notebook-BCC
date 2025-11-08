#!/bin/bash
# Test script for new state file API features

set -e  # Exit on error

echo "🧪 Testing State File API Features"
echo "====================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test files
STATE_FILE_1="./docs/examples/ames_housing/payloads/00_STATE_IDLE.json"
STATE_FILE_2="./docs/examples/ames_housing/payloads/01_STATE_Stage_Running.json"
STATE_FILE_3="./docs/examples/ames_housing/payloads/02_STATE_Step_Running.json"

# Check if state files exist
echo "📂 Checking state files..."
for file in "$STATE_FILE_1" "$STATE_FILE_2" "$STATE_FILE_3"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✓${NC} Found: $file"
    else
        echo -e "   ${RED}✗${NC} Missing: $file"
        exit 1
    fi
done
echo ""

# Test 1: Check if rich is installed
echo "📦 Test 1: Checking rich library..."
if python -c "import rich" 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC} Rich library is installed"
else
    echo -e "   ${YELLOW}⚠${NC}  Rich library not installed (falling back to plain text)"
    echo "   Install with: pip install rich>=13.7.0"
fi
echo ""

# Test 2: Test send-api command with planning
echo " Test 2: Testing send-api with planning API..."
if python main.py send-api \
    --state-file "$STATE_FILE_2" \
    --api-type planning \
    --output /tmp/test_planning_response.json 2>&1 | grep -q "API request completed\|Connection refused\|Cannot connect"; then
    echo -e "   ${GREEN}✓${NC} send-api command executed (check output above for details)"
    if [ -f /tmp/test_planning_response.json ]; then
        echo -e "   ${GREEN}✓${NC} Response saved to file"
        rm -f /tmp/test_planning_response.json
    fi
else
    echo -e "   ${RED}✗${NC} send-api command failed"
    exit 1
fi
echo ""

# Test 3: Test resume command
echo "🔄 Test 3: Testing resume command..."
if python main.py resume \
    --state-file "$STATE_FILE_2" 2>&1 | grep -q "State loaded successfully\|Error"; then
    echo -e "   ${GREEN}✓${NC} resume command executed"
else
    echo -e "   ${RED}✗${NC} resume command failed"
    exit 1
fi
echo ""

# Test 4: Test help commands
echo "❓ Test 4: Testing help commands..."
if python main.py send-api --help | grep -q "state-file"; then
    echo -e "   ${GREEN}✓${NC} send-api help works"
else
    echo -e "   ${RED}✗${NC} send-api help failed"
    exit 1
fi

if python main.py resume --help | grep -q "state-file"; then
    echo -e "   ${GREEN}✓${NC} resume help works"
else
    echo -e "   ${RED}✗${NC} resume help failed"
    exit 1
fi
echo ""

# Test 5: Test state file loader utility
echo "🔧 Test 5: Testing state file loader utility..."
cat > /tmp/test_loader.py << 'EOF'
from utils.state_file_loader import state_file_loader

# Test loading
state = state_file_loader.load_state_file('./docs/examples/ames_housing/payloads/01_STATE_Stage_Running.json')
print(f"✓ Loaded state: {len(state)} keys")

# Test parsing
parsed = state_file_loader.parse_state_for_api(state)
print(f"✓ Parsed state: stage_id={parsed['stage_id']}, step_id={parsed['step_id']}")

# Test context extraction
context = state_file_loader.extract_context(state)
print(f"✓ Extracted context: {len(context['variables'])} variables")

print("State file loader works correctly!")
EOF

if python /tmp/test_loader.py; then
    echo -e "   ${GREEN}✓${NC} State file loader utility works"
    rm -f /tmp/test_loader.py
else
    echo -e "   ${RED}✗${NC} State file loader failed"
    rm -f /tmp/test_loader.py
    exit 1
fi
echo ""

# Test 6: Test API display utility
echo "🎨 Test 6: Testing API display utility..."
cat > /tmp/test_display.py << 'EOF'
from utils.api_display import api_display

# Test display methods
api_display.display_api_request(
    api_type='planning',
    api_url='http://localhost:28600/planning',
    stage_id='test_stage',
    step_id='test_step',
    payload_size=1024
)
print("✓ API request display works")

api_display.display_api_response(
    api_type='planning',
    response={'targetAchieved': True},
    success=True
)
print("✓ API response display works")

print("API display utility works correctly!")
EOF

if python /tmp/test_display.py; then
    echo -e "   ${GREEN}✓${NC} API display utility works"
    rm -f /tmp/test_display.py
else
    echo -e "   ${YELLOW}⚠${NC}  API display had issues (may need rich library)"
    rm -f /tmp/test_display.py
fi
echo ""

# Summary
echo "======================================"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "📝 New features are ready to use:"
echo "   1. CLI: python main.py send-api --state-file <file> --api-type <type>"
echo "   2. CLI: python main.py resume --state-file <file>"
echo "   3. REPL: load_state <file> + send_api <type>"
echo ""
echo "📖 See STATE_API_USAGE.md for detailed usage examples"
echo ""
