#!/bin/bash

# Quick test of the production fixes
echo "Testing SwiftGen V2 with Production Fixes"
echo "========================================="

# Test 1: Simple timer with Grok (should work)
echo ""
echo "Test 1: Timer app with Grok"
curl -X POST http://localhost:8000/api/generate/production \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a simple timer app",
    "app_name": "SimpleTimer",
    "provider": "grok"
  }' | python3 -m json.tool

# Wait for completion
sleep 30

# Test 2: Counter with syntax validation
echo ""
echo "Test 2: Counter app with syntax validation"
curl -X POST http://localhost:8000/api/generate/production \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a counter app",
    "app_name": "Counter",
    "provider": "claude"
  }' | python3 -m json.tool