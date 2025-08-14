@main
struct TimerApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}


import SwiftUI
import Combine

class TimerManager: ObservableObject {
    @Published var timeRemaining: TimeInterval = 0
    @Published var isRunning = false
    @Published var selectedMinutes: Int = 5
    private var timer: AnyCancellable?
    
    func startTimer() {
        timeRemaining = Double(selectedMinutes * 60)
        isRunning = true
        timer = Timer.publish(every: 0.1, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                guard let self = self else { return }
                if self.timeRemaining > 0 {
                    self.timeRemaining -= 0.1
                } else {
                    self.stopTimer()
                    AudioServicesPlaySystemSound(1007)
                }
            }
    }
    
    func stopTimer() {
        timer?.cancel()
        timer = nil
        isRunning = false
    }
    
    func resetTimer() {
        stopTimer()
        timeRemaining = Double(selectedMinutes * 60)
    }
}

struct CircularProgressView: View {
    let progress: Double
    let color: Color
    
    var body: some View {
        ZStack {
            Circle()
                .stroke(color.opacity(0.2), lineWidth: 15)
            Circle()
                .trim(from: 0, to: progress)
                .stroke(color, style: StrokeStyle(lineWidth: 15, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .animation(.easeInOut, value: progress)
        }
    }
}