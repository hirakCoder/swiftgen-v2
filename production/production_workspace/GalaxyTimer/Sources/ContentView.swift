import SwiftUI
import Combine

struct ContentView: View {
    @StateObject private var viewModel = TimerViewModel()
    
    var body: some View {
        VStack(spacing: 40) {
            Text("\(Int(viewModel.timeRemaining)) seconds")
                .font(.system(size: 48, weight: .bold))
                .foregroundStyle(Color(red: 0.8, green: 0.6, blue: 1.0))
            ProgressView(value: viewModel.timeRemaining, total: 60)
                .progressViewStyle(LinearProgressViewStyle(tint: .purple))
            HStack(spacing: 20) {
                Button(action: viewModel.isRunning ? viewModel.stop() : viewModel.start()) {
                    Text(viewModel.isRunning ? "Stop" : "Start")
                }
                    .font(.title2)
                    .padding(.horizontal, 30)
                    .padding(.vertical, 15)
                    .background(LinearGradient(colors: [.purple, .indigo], startPoint: .topLeading, endPoint: .bottomTrailing))
                    .foregroundStyle(.white)
                    .clipShape(Capsule())
                Button(action: viewModel.reset) {
                    Text("Reset")
                }
                    .font(.title2)
                    .padding(.horizontal, 30)
                    .padding(.vertical, 15)
                    .background(Color(red: 0.4, green: 0.2, blue: 0.8))
                    .foregroundStyle(.white)
                    .clipShape(Capsule())
            }
        }
            .padding()
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(LinearGradient(colors: [Color(red: 0.1, green: 0.0, blue: 0.2), Color(red: 0.2, green: 0.0, blue: 0.3)], startPoint: .top, endPoint: .bottom))
    }

}