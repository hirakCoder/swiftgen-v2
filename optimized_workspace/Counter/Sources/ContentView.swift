import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = CounterViewModel()
    @State private var showHistory = false
    @State private var isEditing = false
    
    var body: some View {
        ZStack {
            RadialGradient(
                gradient: Gradient(colors: [.blue.opacity(0.3), .purple.opacity(0.3)]),
                center: .center,
                startRadius: 0,
                endRadius: 300
            )
            .ignoresSafeArea()
            
            VStack(spacing: 30) {
                Text("\(viewModel.count)")
                    .font(.system(size: 80, weight: .bold, design: .rounded))
                    .foregroundColor(.primary)
                    .contentTransition(.numericText())
                    .animation(.spring(), value: viewModel.count)
                
                HStack(spacing: 20) {
                    CounterButton(systemName: "minus.circle.fill") {
                        viewModel.decrement()
                    }
                    
                    CounterButton(systemName: "plus.circle.fill") {
                        viewModel.increment()
                    }
                }
                
                VStack {
                    Text("Increment Amount")
                        .font(.caption)
                    
                    Slider(value: .convert(from: $viewModel.incrementAmount), in: 1...10, step: 1)
                        .padding(.horizontal)
                    
                    Text("\(viewModel.incrementAmount)")
                        .font(.caption2)
                }
                .padding()
                .background(.ultraThinMaterial)
                .clipShape(RoundedRectangle(cornerRadius: 15))
                
                if let lastChange = viewModel.lastChangeTime {
                    Text("Last changed: \(lastChange, style: .relative)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Button("Show History") {
                    showHistory.toggle()
                }
                .sheet(isPresented: $showHistory) {
                    HistoryView(history: viewModel.changeHistory)
                }
            }
            .padding()
        }
    }
}

struct CounterButton: View {
    let systemName: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.system(size: 44))
                .foregroundColor(.primary)
        }
        .buttonStyle(BounceButtonStyle())
    }
}

struct BounceButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.9 : 1)
            .animation(.spring(), value: configuration.isPressed)
    }
}

struct HistoryView: View {
    let history: [(amount: Int, date: Date)]
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List(history.indices, id: \.self) { index in
                let item = history[index]
                HStack {
                    Image(systemName: item.amount > 0 ? "plus.circle" : "minus.circle")
                        .foregroundColor(item.amount > 0 ? .green : .red)
                    Text("Changed by \(abs(item.amount))")
                    Spacer()
                    Text(item.date, style: .time)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("History")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                Button("Done") {
                    dismiss()
                }
            }
        }
    }
}

extension Binding where Value == Double {
    static func convert(from binding: Binding<Int>) -> Binding<Double> {
        Binding<Double>(
            get: { Double(binding.wrappedValue) },
            set: { binding.wrappedValue = Int($0) }
        )
    }
}