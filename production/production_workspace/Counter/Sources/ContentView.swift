import SwiftUI
import Combine

struct ContentView: View {
    @StateObject private var viewModel = CounterViewModel()
    
    var body: some View {
        VStack(spacing: 30) {
            Text("\(viewModel.count)")
                .font(.system(size: 72, weight: .bold, design: .rounded))
                .foregroundStyle(.primary)
            HStack(spacing: 20) {
                Button(action: viewModel.decrement) {
                    Text("-")
                }
                    .font(.largeTitle)
                    .frame(width: 80, height: 80)
                    .background(.blue)
                    .foregroundStyle(.white)
                    .clipShape(Circle())
                Button(action: viewModel.increment) {
                    Text("+")
                }
                    .font(.largeTitle)
                    .frame(width: 80, height: 80)
                    .background(.blue)
                    .foregroundStyle(.white)
                    .clipShape(Circle())
            }
            Button(action: viewModel.reset) {
                Text("Reset")
            }
                .font(.headline)
                .padding()
                .background(.secondary)
                .foregroundStyle(.white)
                .clipShape(Capsule())
        }
            .padding()
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(.systemBackground))
    }

}