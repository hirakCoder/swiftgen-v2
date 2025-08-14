import SwiftUI

@main
struct CounterApp: App {
    @StateObject private var counterViewModel = CounterViewModel()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(counterViewModel)
        }
    }
}

class CounterViewModel: ObservableObject {
    @Published private(set) var count: Int = 0
    @Published private(set) var lastAction: String = ""
    @Published private(set) var milestone: String = ""
    
    func increment() {
        count += 1
        lastAction = "Incremented"
        checkMilestone()
    }
    
    func decrement() {
        count -= 1
        lastAction = "Decremented"
        checkMilestone()
    }
    
    func reset() {
        count = 0
        lastAction = "Reset"
        milestone = ""
    }
    
    private func checkMilestone() {
        switch count {
        case 10: milestone = "🎉 Reached 10!"
        case 25: milestone = "🌟 Quarter to 100!"
        case 50: milestone = "⭐️ Halfway there!"
        case 100: milestone = "🏆 Century achieved!"
        default: break
        }
    }
}