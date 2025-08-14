@main
struct CalculatorApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.dark)
        }
    }
}

import SwiftUI
import Combine

class CalculatorModel: ObservableObject {
    @Published var display = "0"
    @Published var currentOperation: Operation? = nil
    @Published var previousNumber: Double? = nil
    private var isTypingNumber = false
    
    enum Operation: String {
        case add = "+"
        case subtract = "−"
        case multiply = "×"
        case divide = "÷"
    }
    
    func addDigit(_ digit: String) {
        if !isTypingNumber {
            display = digit
            isTypingNumber = true
        } else {
            display += digit
        }
    }
    
    func setOperation(_ operation: Operation) {
        if let number = Double(display) {
            if let prev = previousNumber, let currentOp = currentOperation {
                calculate()
            } else {
                previousNumber = number
            }
        }
        currentOperation = operation
        isTypingNumber = false
    }
    
    func calculate() {
        guard let number1 = previousNumber,
              let number2 = Double(display),
              let operation = currentOperation else { return }
        
        let result: Double
        switch operation {
        case .add: result = number1 + number2
        case .subtract: result = number1 - number2
        case .multiply: result = number1 * number2
        case .divide: result = number2 != 0 ? number1 / number2 : 0
        }
        
        display = String(format: "%g", result)
        previousNumber = nil
        currentOperation = nil
        isTypingNumber = false
    }
    
    func clear() {
        display = "0"
        currentOperation = nil
        previousNumber = nil
        isTypingNumber = false
    }
}

struct CalculatorButton: View {
    let title: String
    let color: Color
    let width: CGFloat
    let action: () -> Void
    
    @State private var isPressed = false
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.title)
                .fontWeight(.medium)
                .frame(width: width, height: width)
                .background(color)
                .foregroundColor(.white)
                .clipShape(Circle())
                .scaleEffect(isPressed ? 0.9 : 1.0)
        }
        .buttonStyle(PlainButtonStyle())
        .pressEvents(onPress: { isPressed = true },
                    onRelease: { isPressed = false })
    }
}