#!/bin/bash

# Production Test Suite for SwiftGen V2
# Tests various app types and modifications

echo "============================================"
echo "SwiftGen V2 Production Test Suite"
echo "============================================"
echo ""

# Test configuration
BASE_URL="http://localhost:8000/api"
RESULTS_FILE="test_results_$(date +%Y%m%d_%H%M%S).txt"

# Function to test app generation
test_generation() {
    local description="$1"
    local app_name="$2"
    local provider="$3"
    
    echo "Testing: $app_name ($provider)"
    START_TIME=$(date +%s)
    
    RESPONSE=$(curl -s -X POST "$BASE_URL/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"description\": \"$description\",
            \"app_name\": \"$app_name\",
            \"provider\": \"$provider\"
        }")
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # Extract success status
    SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('success', False))" 2>/dev/null)
    PROJECT_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('project_id', 'unknown'))" 2>/dev/null)
    
    if [ "$SUCCESS" = "True" ]; then
        echo "  ✅ SUCCESS in ${DURATION}s (Project: $PROJECT_ID)"
        
        # Check if templates were used
        if [ -d "workspaces/$PROJECT_ID/Sources" ]; then
            FILE_COUNT=$(ls workspaces/$PROJECT_ID/Sources/*.swift 2>/dev/null | wc -l)
            echo "  📁 Generated $FILE_COUNT Swift files"
            
            # Check for template indicators
            TEMPLATE_CHECK=$(grep -l "// Template" workspaces/$PROJECT_ID/Sources/*.swift 2>/dev/null | wc -l)
            if [ "$TEMPLATE_CHECK" -eq 0 ]; then
                echo "  ✅ No templates detected"
            else
                echo "  ⚠️ WARNING: Template usage detected!"
            fi
        fi
    else
        ERROR=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', 'Unknown error'))" 2>/dev/null)
        echo "  ❌ FAILED in ${DURATION}s"
        echo "     Error: $ERROR"
    fi
    
    echo "$app_name,$provider,$SUCCESS,$DURATION" >> "$RESULTS_FILE"
    return $([ "$SUCCESS" = "True" ] && echo 0 || echo 1)
}

# Function to test modification
test_modification() {
    local project_id="$1"
    local modification="$2"
    
    echo "  Testing modification: $modification"
    START_TIME=$(date +%s)
    
    RESPONSE=$(curl -s -X POST "$BASE_URL/modify" \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\": \"$project_id\",
            \"modifications\": \"$modification\",
            \"provider\": \"claude\"
        }")
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('success', False))" 2>/dev/null)
    
    if [ "$SUCCESS" = "True" ]; then
        echo "    ✅ Modification successful in ${DURATION}s"
    else
        echo "    ❌ Modification failed in ${DURATION}s"
    fi
    
    return $([ "$SUCCESS" = "True" ] && echo 0 || echo 1)
}

# Initialize counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo "🧪 PHASE 1: Testing Different App Types"
echo "----------------------------------------"

# Test 1: Simple Counter App
test_generation "Create a counter app with increment and decrement buttons" "Counter" "claude"
[ $? -eq 0 ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
((TOTAL_TESTS++))
echo ""

# Test 2: Todo List App
test_generation "Build a todo list app with add, delete, and mark complete features" "TodoList" "gpt4"
[ $? -eq 0 ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
((TOTAL_TESTS++))
echo ""

# Test 3: Weather App
test_generation "Create a weather app showing current temperature and 5-day forecast" "Weather" "claude"
[ $? -eq 0 ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
((TOTAL_TESTS++))
echo ""

# Test 4: Calculator App
test_generation "Make a calculator app with basic arithmetic operations" "Calculator" "grok"
[ $? -eq 0 ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
((TOTAL_TESTS++))
echo ""

# Test 5: Timer App
test_generation "Build a timer app with start, stop, and reset functionality" "Timer" "claude"
TIMER_SUCCESS=$?
[ $TIMER_SUCCESS -eq 0 ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
((TOTAL_TESTS++))
TIMER_PROJECT_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('project_id', ''))" 2>/dev/null)
echo ""

echo "🧪 PHASE 2: Testing Modifications"
echo "----------------------------------------"

if [ ! -z "$TIMER_PROJECT_ID" ] && [ "$TIMER_SUCCESS" -eq 0 ]; then
    test_modification "$TIMER_PROJECT_ID" "Add a dark mode toggle"
    [ $? -eq 0 ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
    
    test_modification "$TIMER_PROJECT_ID" "Add sound effects when timer ends"
    [ $? -eq 0 ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
else
    echo "  ⚠️ Skipping modifications (no successful app to modify)"
fi
echo ""

echo "🧪 PHASE 3: Testing Uniqueness"
echo "----------------------------------------"
echo "Generating same app 3 times to verify uniqueness..."

for i in 1 2 3; do
    test_generation "Create a simple notes app" "Notes$i" "claude"
    [ $? -eq 0 ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
done

# Compare generated files for uniqueness
if [ -d "workspaces" ]; then
    NOTES1_CONTENT=$(cat workspaces/*/Sources/ContentView.swift 2>/dev/null | head -100 | md5)
    NOTES2_CONTENT=$(cat workspaces/*/Sources/ContentView.swift 2>/dev/null | tail -100 | md5)
    
    if [ "$NOTES1_CONTENT" != "$NOTES2_CONTENT" ]; then
        echo "✅ Apps are unique (different implementations)"
    else
        echo "⚠️ Apps might be using templates (similar implementations)"
    fi
fi
echo ""

echo "============================================"
echo "📊 TEST RESULTS SUMMARY"
echo "============================================"
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS ($(( PASSED_TESTS * 100 / TOTAL_TESTS ))%)"
echo "Failed: $FAILED_TESTS"
echo ""

# Performance Analysis
if [ -f "$RESULTS_FILE" ]; then
    AVG_TIME=$(awk -F',' '{sum+=$4; count++} END {print sum/count}' "$RESULTS_FILE")
    echo "Average Generation Time: ${AVG_TIME}s"
fi

echo "Detailed results saved to: $RESULTS_FILE"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED - PRODUCTION READY!"
else
    echo "⚠️ SOME TESTS FAILED - NEEDS ATTENTION"
fi

exit $FAILED_TESTS