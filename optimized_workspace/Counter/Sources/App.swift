@main
struct CounterApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}


import SwiftUI
import Combine

class CounterViewModel: ObservableObject {
    @Published var count = 0
    @Published var incrementAmount = 1
    @Published var lastChangeTime: Date? = nil
    @Published var changeHistory: [(amount: Int, date: Date)] = []
    
    func increment() {
        count += incrementAmount
        updateHistory(amount: incrementAmount)
    }
    
    func decrement() {
        count -= incrementAmount
        updateHistory(amount: -incrementAmount)
    }
    
    private func updateHistory(amount: Int) {
        lastChangeTime = Date()
        changeHistory.append((amount: amount, date: Date()))
        if changeHistory.count > 10 {
            changeHistory.removeFirst()
        }
    }
}