# Known Issues - SwiftGen V2

## Incorrect Logging for Modifications (August 7, 2025)

### Issue Description
When modifying existing apps using phrases that contain creation keywords (like "make", "create", "build", "design", "develop"), the intelligent_llm_router.py incorrectly logs these as "Is creation request: True" even though they are modifications.

### Affected Phrases
- "make it more colorful"
- "make the app beautiful"
- "build a better UI"
- "create a settings page"
- "design a new icon"
- "develop additional features"
- "make this faster"
- "create new animations"

### Current Behavior
- **Functionality**: ✅ Works correctly - modifications are successfully applied
- **Logging**: ❌ Incorrect - shows "Is creation request: True" in logs

### Technical Details
The issue occurs in `backend/intelligent_llm_router.py` in the `analyze_request()` method. The creation patterns are matching too broadly on keywords like "make", "create", "build" without considering the full context.

### Attempted Fixes
1. Added modification indicators list to detect common modification patterns
2. Implemented override logic to force is_creation=False when modification patterns detected
3. Added debug logging to trace execution flow

### Why Fix Didn't Work
The code changes were properly saved to the file but weren't executing at runtime, possibly due to:
- Python module caching
- A different code path being used (enhanced_claude_service.py correctly passes is_modification_context=True internally)

### Impact
- **User Impact**: None - functionality works correctly
- **Developer Impact**: Confusing logs that show incorrect classification
- **Severity**: Low - cosmetic issue only

### Workaround
The system works correctly because `enhanced_claude_service.py` passes `is_modification_context=True` when calling `modify_ios_app`, ensuring proper modification handling despite incorrect initial routing logs.

### Resolution Status
**Unresolved** - User decided to leave as-is since functionality works correctly. The issue is noted here for future reference if someone wants to investigate further.

### Test Results
From comprehensive_test.py:
- All modifications work successfully
- Generation still works correctly
- Logs incorrectly show "Is creation request: True" for modification phrases with creation keywords

### Future Considerations
If this needs to be fixed in the future:
1. Check if the router is being bypassed by another component
2. Investigate Python module caching issues
3. Consider restructuring the pattern matching to be more context-aware
4. Look into why is_modification_context parameter isn't being passed correctly from the API endpoint