"""
Grok File Completer
Ensures all referenced types have corresponding files generated
"""

import re
import logging

logger = logging.getLogger(__name__)

class GrokFileCompleter:
    """Complete missing files that Grok references but doesn't generate"""
    
    @staticmethod
    def complete_missing_files(files: list) -> list:
        """Ensure all referenced types have files"""
        
        # Extract all type references
        referenced_types = set()
        existing_types = set()
        
        for file_info in files:
            content = file_info.get('content', '')
            path = file_info.get('path', '')
            
            # Find existing type definitions
            struct_matches = re.findall(r'struct\s+(\w+)(?:\s*:|\s*{)', content)
            class_matches = re.findall(r'class\s+(\w+)(?:\s*:|\s*{)', content)
            existing_types.update(struct_matches)
            existing_types.update(class_matches)
            
            # Find referenced types
            # Pattern: @StateObject private var xxx = TypeName()
            ref_matches = re.findall(r'=\s*(\w+)\(\)', content)
            referenced_types.update(ref_matches)
            
            # Pattern: : TypeName in property declarations
            type_matches = re.findall(r':\s*(\w+)(?:\s|$|,|\))', content)
            referenced_types.update(type_matches)
        
        # Find missing types
        missing_types = referenced_types - existing_types
        
        # Filter out built-in types
        swift_builtins = {
            'Int', 'String', 'Bool', 'Double', 'Float', 'Array', 'Dictionary',
            'Set', 'Optional', 'View', 'Scene', 'App', 'ObservableObject',
            'Published', 'State', 'StateObject', 'ObservedObject', 'Binding',
            'EnvironmentObject', 'Environment', 'Text', 'Button', 'VStack',
            'HStack', 'ZStack', 'NavigationStack', 'NavigationView', 'List',
            'ForEach', 'ScrollView', 'Image', 'Color', 'Font', 'Spacer',
            'EmptyView', 'AnyView', 'GeometryReader', 'Path', 'Shape',
            'PreviewProvider', 'ContentView', 'Timer', 'Date', 'TimeInterval',
            'UIImpactFeedbackGenerator', 'Combine', 'SwiftUI', 'Foundation'
        }
        
        missing_types = missing_types - swift_builtins
        
        # Generate missing files
        new_files = []
        for type_name in missing_types:
            if 'ViewModel' in type_name:
                # Generate a ViewModel file
                new_files.append(GrokFileCompleter._generate_view_model(type_name))
                logger.info(f"[GROK COMPLETE] Generated missing {type_name}")
            elif 'View' in type_name:
                # Generate a View file
                new_files.append(GrokFileCompleter._generate_view(type_name))
                logger.info(f"[GROK COMPLETE] Generated missing {type_name}")
            elif 'Model' in type_name:
                # Generate a Model file
                new_files.append(GrokFileCompleter._generate_model(type_name))
                logger.info(f"[GROK COMPLETE] Generated missing {type_name}")
        
        # Combine original and new files
        all_files = files + new_files
        
        if new_files:
            logger.info(f"[GROK COMPLETE] Added {len(new_files)} missing files")
        
        return all_files
    
    @staticmethod
    def _generate_view_model(type_name: str) -> dict:
        """Generate a basic ViewModel"""
        
        # Determine the app type from the name
        if 'Timer' in type_name:
            content = """import SwiftUI
import Combine
import Foundation

@MainActor
class TimerViewModel: ObservableObject {
    @Published var timeRemaining: TimeInterval = 60
    @Published var isRunning: Bool = false
    @Published var totalTime: TimeInterval = 60
    
    private var timer: Timer?
    
    func startTimer() {
        isRunning = true
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            Task { @MainActor in
                if self.timeRemaining > 0 {
                    self.timeRemaining -= 1
                } else {
                    self.stopTimer()
                }
            }
        }
    }
    
    func stopTimer() {
        isRunning = false
        timer?.invalidate()
        timer = nil
    }
    
    func resetTimer() {
        stopTimer()
        timeRemaining = totalTime
    }
    
    func setTime(_ seconds: TimeInterval) {
        totalTime = seconds
        timeRemaining = seconds
    }
}"""
        elif 'Counter' in type_name:
            content = """import SwiftUI
import Combine

@MainActor
class CounterViewModel: ObservableObject {
    @Published var count: Int = 0
    @Published var stepSize: Int = 1
    
    func increment() {
        count += stepSize
    }
    
    func decrement() {
        count -= stepSize
    }
    
    func reset() {
        count = 0
    }
}"""
        elif 'Dice' in type_name:
            content = """import SwiftUI
import Combine

@MainActor
class DiceViewModel: ObservableObject {
    @Published var diceValue: Int = 1
    @Published var numberOfDice: Int = 1
    @Published var rollResults: [Int] = []
    @Published var isRolling: Bool = false
    
    func rollDice() {
        isRolling = true
        rollResults = []
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            for _ in 0..<self.numberOfDice {
                self.rollResults.append(Int.random(in: 1...6))
            }
            self.diceValue = self.rollResults.first ?? 1
            self.isRolling = false
        }
    }
}"""
        else:
            # Generic ViewModel
            content = f"""import SwiftUI
import Combine

@MainActor
class {type_name}: ObservableObject {{
    @Published var isLoading: Bool = false
    @Published var data: String = ""
    
    func refresh() {{
        isLoading = true
        Task {{
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            await MainActor.run {{
                self.data = "Updated"
                self.isLoading = false
            }}
        }}
    }}
}}"""
        
        return {
            'path': f'Sources/ViewModels/{type_name}.swift',
            'content': content
        }
    
    @staticmethod
    def _generate_view(type_name: str) -> dict:
        """Generate a basic View"""
        
        content = f"""import SwiftUI

struct {type_name}: View {{
    var body: some View {{
        Text("{type_name}")
            .padding()
    }}
}}

struct {type_name}_Previews: PreviewProvider {{
    static var previews: some View {{
        {type_name}()
    }}
}}"""
        
        return {
            'path': f'Sources/Views/{type_name}.swift',
            'content': content
        }
    
    @staticmethod
    def _generate_model(type_name: str) -> dict:
        """Generate a basic Model"""
        
        content = f"""import Foundation

struct {type_name}: Identifiable, Codable {{
    let id = UUID()
    var name: String
    var value: String
    var timestamp: Date = Date()
}}"""
        
        return {
            'path': f'Sources/Models/{type_name}.swift',
            'content': content
        }