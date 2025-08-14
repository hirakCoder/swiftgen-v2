import SwiftUI
import Combine

struct ContentView: View {
    @StateObject private var viewModel = CounterViewModel()
    
    var body: some View {
        VStack(spacing: 30) {
            Text("\(viewModel.count)")
                .font(.system(size: 72, weight: .bold, design: .rounded))
                .foregroundStyle(Color(red: 1.0, green: 0.4, blue: 0.2))
            HStack(spacing: 20) {
                Button(action: viewModel.decrement) {
                    Text("-")
                }
                    .font(.largeTitle)
                    .frame(width: 80, height: 80)
                    .background(LinearGradient(colors: [.red, .orange], startPoint: .top, endPoint: .bottom))
                    .foregroundStyle(.white)
                    .clipShape(Circle())
                Button(action: viewModel.increment) {
                    Text("+")
                }
                    .font(.largeTitle)
                    .frame(width: 80, height: 80)
                    .background(LinearGradient(colors: [.red, .orange], startPoint: .top, endPoint: .bottom))
                    .foregroundStyle(.white)
                    .clipShape(Circle())
            }
            Button(action: viewModel.reset) {
                Text("Reset")
            }
                .font(.headline)
                .padding()
                .background(Color(red: 0.8, green: 0.2, blue: 0.1))
                .foregroundStyle(.white)
                .clipShape(Capsule())
        }
            .padding()
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(LinearGradient(colors: [Color(red: 0.4, green: 0.1, blue: 0.0), Color(red: 0.6, green: 0.2, blue: 0.1)], startPoint: .topLeading, endPoint: .bottomTrailing))
    }

}