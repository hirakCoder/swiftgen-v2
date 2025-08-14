import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var viewModel: CounterViewModel
    @State private var isAnimating = false
    
    var body: some View {
        ZStack {
            RadialGradient(
                gradient: Gradient(colors: [.blue.opacity(0.3), .purple.opacity(0.3)]),
                center: .center,
                startRadius: 100,
                endRadius: 400
            )
            .ignoresSafeArea()
            
            VStack(spacing: 30) {
                counterDisplay
                actionButtons
                lastActionDisplay
                milestoneDisplay
            }
            .padding()
        }
    }
    
    private var counterDisplay: some View {
        Text("\(viewModel.count)")
            .font(.system(size: 80, weight: .bold, design: .rounded))
            .foregroundColor(.primary)
            .contentTransition(.numericText())
            .scaleEffect(isAnimating ? 1.2 : 1.0)
            .animation(.spring(response: 0.3), value: isAnimating)
    }
    
    private var actionButtons: some View {
        HStack(spacing: 20) {
            CounterButton(icon: "minus.circle.fill", color: .red) {
                animate { viewModel.decrement() }
            }
            
            CounterButton(icon: "arrow.counterclockwise.circle.fill", color: .gray) {
                animate { viewModel.reset() }
            }
            
            CounterButton(icon: "plus.circle.fill", color: .green) {
                animate { viewModel.increment() }
            }
        }
    }
    
    private var lastActionDisplay: some View {
        Text(viewModel.lastAction)
            .font(.caption)
            .foregroundColor(.secondary)
            .opacity(viewModel.lastAction.isEmpty ? 0 : 1)
            .animation(.easeInOut, value: viewModel.lastAction)
    }
    
    private var milestoneDisplay: some View {
        Text(viewModel.milestone)
            .font(.title3)
            .foregroundColor(.primary)
            .opacity(viewModel.milestone.isEmpty ? 0 : 1)
            .transition(.scale.combined(with: .opacity))
            .animation(.spring(), value: viewModel.milestone)
    }
    
    private func animate(_ action: @escaping () -> Void) {
        isAnimating = true
        action()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            isAnimating = false
        }
    }
}

struct CounterButton: View {
    let icon: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.system(size: 44))
                .foregroundColor(color)
        }
        .buttonStyle(.plain)
    }
}