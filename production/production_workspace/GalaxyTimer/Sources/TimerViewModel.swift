import SwiftUI
import Combine

@MainActor
final class TimerViewModelViewModel: ObservableObject {
    @Published var timeRemaining: TimeInterval = 60
    @Published var isRunning: Bool = false
    private var timer: Timer?
    
    func start() {
        isRunning = true
                timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { _ in
                    if self.timeRemaining > 0 {
                        self.timeRemaining -= 1
                    } else {
                        self.stop()
                    }
                }
    }
    func stop() {
        isRunning = false
                timer?.invalidate()
                timer = nil
    }
    func reset() {
        stop()
                timeRemaining = 60
    }
}