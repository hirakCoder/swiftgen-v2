import SwiftUI
import Combine

struct ContentView: View {
    @StateObject private var viewModel = TimerViewModel()
    
    var body: some View {
        VStack(spacing: 40) {
            Text("\(Int(viewModel.timeRemaining)) seconds")
                .font(.system(size: 48, weight: .bold))
                .foregroundStyle(.primary)
            ProgressView(value: viewModel.timeRemaining, total: 60)
                .progressViewStyle(LinearProgressViewStyle(tint: .blue))
            HStack(spacing: 20) {
                Button(action: viewModel.isRunning ? viewModel.stop() : viewModel.start()) {
                    Text(viewModel.isRunning ? "Stop" : "Start")
                }
                    .font(.title2)
                    .padding(.horizontal, 30)
                    .padding(.vertical, 15)
                    .background(.blue)
                    .foregroundStyle(.white)
                    .clipShape(Capsule())
                Button(action: viewModel.reset) {
                    Text("Reset")
                }
                    .font(.title2)
                    .padding(.horizontal, 30)
                    .padding(.vertical, 15)
                    .background(.secondary)
                    .foregroundStyle(.white)
                    .clipShape(Capsule())
            }
        }
            .padding()
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(.systemBackground))
    }

}