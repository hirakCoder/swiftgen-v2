"""
Test suite for error handling and auto-fix mechanism
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.error_handler import SwiftErrorAutoFixer, ErrorType
import tempfile
import shutil

def test_missing_import_fix():
    """Test fixing missing imports"""
    fixer = SwiftErrorAutoFixer()
    
    # Create test file with missing import
    test_content = """
struct ContentView: View {
    var body: some View {
        Button("Test") {
            let feedback = UIImpactFeedbackGenerator(style: .medium)
            feedback.impactOccurred()
        }
    }
}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False) as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # Simulate error
        error_output = "cannot find type 'UIImpactFeedbackGenerator' in scope"
        errors = fixer.detect_errors(error_output)
        
        assert len(errors) > 0, "Should detect missing import error"
        
        # Apply fix
        for error_pattern, error_text in errors:
            fixer.fix_file(temp_file, error_pattern, error_text)
        
        # Check fix was applied
        with open(temp_file, 'r') as f:
            fixed_content = f.read()
        
        assert 'import UIKit' in fixed_content, "Should add UIKit import"
        print("✅ Missing import fix test passed")
        
    finally:
        os.unlink(temp_file)

def test_swiftui_inheritance_fix():
    """Test fixing SwiftUI inheritance issues"""
    fixer = SwiftErrorAutoFixer()
    
    # Create test file with inheritance error
    test_content = """
@main
struct TestApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False) as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # Simulate error
        error_output = "inheritance from non-protocol type 'App'"
        errors = fixer.detect_errors(error_output)
        
        assert len(errors) > 0, "Should detect inheritance error"
        
        # Apply fix
        for error_pattern, error_text in errors:
            fixer.fix_file(temp_file, error_pattern, error_text)
        
        # Check fix was applied
        with open(temp_file, 'r') as f:
            fixed_content = f.read()
        
        assert 'import SwiftUI' in fixed_content, "Should add SwiftUI import"
        print("✅ SwiftUI inheritance fix test passed")
        
    finally:
        os.unlink(temp_file)

def test_duplicate_declaration_fix():
    """Test fixing duplicate declarations"""
    fixer = SwiftErrorAutoFixer()
    
    # Create test file with duplicate @MainActor
    test_content = """
import SwiftUI

@MainActor
@MainActor
class ViewModel: ObservableObject {
    @Published var count = 0
}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False) as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # Simulate error
        error_output = "redeclaration of '@MainActor'"
        errors = fixer.detect_errors(error_output)
        
        assert len(errors) > 0, "Should detect duplicate declaration"
        
        # Apply fix
        for error_pattern, error_text in errors:
            fixer.fix_file(temp_file, error_pattern, error_text)
        
        # Check fix was applied
        with open(temp_file, 'r') as f:
            fixed_content = f.read()
        
        # Count @MainActor occurrences
        mainactor_count = fixed_content.count('@MainActor')
        assert mainactor_count == 1, "Should have only one @MainActor"
        print("✅ Duplicate declaration fix test passed")
        
    finally:
        os.unlink(temp_file)

def test_bracket_fix():
    """Test fixing mismatched brackets"""
    fixer = SwiftErrorAutoFixer()
    
    # Create test file with missing closing brace
    test_content = """
import SwiftUI

struct ContentView: View {
    var body: some View {
        VStack {
            Text("Hello")
        
    }
}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False) as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # Apply bracket fix
        fixed = fixer._fix_brackets(test_content)
        
        # Count brackets
        open_count = fixed.count('{')
        close_count = fixed.count('}')
        
        assert open_count == close_count, "Brackets should be balanced"
        print("✅ Bracket fix test passed")
        
    finally:
        os.unlink(temp_file)

def test_full_compilation_fix():
    """Test full compilation error fixing workflow"""
    fixer = SwiftErrorAutoFixer()
    
    # Create a test project structure
    test_dir = tempfile.mkdtemp()
    sources_dir = os.path.join(test_dir, 'Sources')
    os.makedirs(sources_dir)
    
    # Create problematic Swift file
    test_file = os.path.join(sources_dir, 'ContentView.swift')
    with open(test_file, 'w') as f:
        f.write("""
struct ContentView: View {
    var body: some View {
        Button("Test") {
            let feedback = UIImpactFeedbackGenerator(style: .medium)
            feedback.impactOccurred()
        }
    }
}
""")
    
    try:
        # Simulate compilation error
        error_output = """
ContentView.swift:2:22: error: cannot find type 'View' in scope
struct ContentView: View {
                     ^~~~
ContentView.swift:5:28: error: cannot find type 'UIImpactFeedbackGenerator' in scope
            let feedback = UIImpactFeedbackGenerator(style: .medium)
                           ^~~~~~~~~~~~~~~~~~~~~~~~~~
"""
        
        # Apply fixes
        result = fixer.auto_fix_compilation_errors(error_output, test_dir)
        
        assert result["success"], "Should successfully fix errors"
        assert result["fixed_count"] > 0, "Should fix at least one error"
        
        # Verify fixes were applied
        with open(test_file, 'r') as f:
            fixed_content = f.read()
        
        assert 'import SwiftUI' in fixed_content or 'import UIKit' in fixed_content, "Should add necessary imports"
        
        print("✅ Full compilation fix test passed")
        print(fixer.generate_fix_report())
        
    finally:
        shutil.rmtree(test_dir)

def run_all_tests():
    """Run all error handling tests"""
    print("🧪 Running error handling tests...\n")
    
    tests = [
        test_missing_import_fix,
        test_swiftui_inheritance_fix,
        test_duplicate_declaration_fix,
        test_bracket_fix,
        test_full_compilation_fix
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)