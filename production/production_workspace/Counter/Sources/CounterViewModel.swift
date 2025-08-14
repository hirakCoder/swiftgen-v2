import SwiftUI
import Combine

@MainActor
final class CounterViewModelViewModel: ObservableObject {
    @Published var count: Int = 0
    
    func increment() {
        count += 1
    }
    func decrement() {
        count -= 1
    }
    func reset() {
        count = 0
    }
}