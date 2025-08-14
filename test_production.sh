#!/bin/bash

# SwiftGen V2 Production Testing Script
# Tests the production endpoint with all fixes applied

echo "======================================"
echo "SwiftGen V2 Production Testing"
echo "======================================"

# Base URL
BASE_URL="http://localhost:8000/api/generate/production"

# Function to test an app
test_app() {
    local description="$1"
    local app_name="$2"
    local provider="$3"
    
    echo ""
    echo "Testing: $app_name ($provider)"
    echo "Description: $description"
    echo "---"
    
    # Make the request
    response=$(curl -s -X POST "$BASE_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"description\": \"$description\",
            \"app_name\": \"$app_name\",
            \"provider\": \"$provider\"
        }")
    
    # Check if successful
    if echo "$response" | grep -q '"success":true'; then
        echo "✅ SUCCESS: $app_name generated successfully!"
    else
        echo "❌ FAILED: $app_name generation failed"
        echo "Response: $response"
    fi
    
    # Wait a bit between tests
    sleep 2
}

# Test Suite 1: Simple Apps with Grok (UI specialist)
echo ""
echo "TEST SUITE 1: Simple Apps (Grok)"
echo "================================"
test_app "Create a beautiful timer app with gradient background" "BeautifulTimer" "grok"
test_app "Create a counter app with smooth animations" "AnimatedCounter" "grok"
test_app "Create a calculator with modern design" "ModernCalc" "grok"

# Test Suite 2: Logic Apps with GPT-4 (Algorithm specialist)
echo ""
echo "TEST SUITE 2: Logic Apps (GPT-4)"
echo "================================"
test_app "Create a sorting algorithm visualizer" "SortVisualizer" "gpt4"
test_app "Create a fibonacci calculator with optimization" "FibCalc" "gpt4"
test_app "Create a prime number checker with efficient algorithm" "PrimeChecker" "gpt4"

# Test Suite 3: Architecture Apps with Claude (Architecture specialist)
echo ""
echo "TEST SUITE 3: Architecture Apps (Claude)"
echo "======================================="
test_app "Create a todo app with MVVM architecture" "TodoMVVM" "claude"
test_app "Create a notes app with proper data persistence" "NotesApp" "claude"
test_app "Create a weather app with clean architecture" "WeatherArch" "claude"

# Test Suite 4: Hybrid Mode (All 3 LLMs)
echo ""
echo "TEST SUITE 4: Hybrid Mode"
echo "========================"
test_app "Create a complex e-commerce app with beautiful UI, efficient search, and MVVM architecture" "ShopApp" "hybrid"

echo ""
echo "======================================"
echo "Testing Complete!"
echo "======================================