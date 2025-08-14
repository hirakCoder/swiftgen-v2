import SwiftUI
import Combine

class CalculatorModel: ObservableObject {
    @Published var displayValue: String = "0"
    @Published var previousValue: Double = 0
    @Published var operation: String? = nil
    private var isNewNumber = true
    
    func addDigit(_ digit: String) {
        if isNewNumber {
            displayValue = digit
            isNewNumber = false
        } else {
            displayValue += digit
        }
    }
    
    func setOperation(_ op: String) {
        operation = op
        previousValue = Double(displayValue) ?? 0
        isNewNumber = true
    }
    
    func calculate() {
        let currentValue = Double(displayValue) ?? 0
        var result: Double = 0
        
        switch operation {
        case "+": result = previousValue + currentValue
        case "-": result = previousValue - currentValue
        case "×": result = previousValue * currentValue
        case "÷": result = previousValue / currentValue
        default: return
        }
        
        displayValue = String(format: "%g", result)
        isNewNumber = true
        operation = nil
    }
    
    func clear() {
        displayValue = "0"
        previousValue = 0
        operation = nil
        isNewNumber = true
    }
}

struct NeonButton: View {
    let title: String
    let color: Color
    let action: () -> Void
    
    @State private var isPressed = false
    
    var body: some View {
        Button(action: {
            action()
            withAnimation(.easeInOut(duration: 0.1)) {
                isPressed = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                withAnimation(.easeInOut(duration: 0.1)) {
                    isPressed = false
                }
            }
        }) {
            Text(title)
                .font(.system(size: 32, weight: .bold, design: .rounded))
                .foregroundColor(.white)
                .frame(width: 70, height: 70)
                .background(color)
                .overlay(
                    RoundedRectangle(cornerRadius: 20)
                        .stroke(color, lineWidth: 4)
                        .blur(radius: isPressed ? 10 : 5)
                )
                .clipShape(RoundedRectangle(cornerRadius: 20))
                .shadow(color: color.opacity(0.6), radius: isPressed ? 15 : 10)
                .scaleEffect(isPressed ? 0.95 : 1.0)
        }
    }
}

struct ContentView: View {
    @StateObject private var calculator = CalculatorModel()
    
    let buttons: [[CalcButton]] = [
        [.clear, .negative, .percent, .divide],
        [.seven, .eight, .nine, .multiply],
        [.four, .five, .six, .subtract],
        [.one, .two, .three, .add],
        [.zero, .decimal, .equals]
    ]
    
    enum CalcButton: String {
        case zero = "0", one = "1", two = "2", three = "3", four = "4"
        case five = "5", six = "6", seven = "7", eight = "8", nine = "9"
        case decimal = ".", equals = "=", add = "+", subtract = "-"
        case multiply = "×", divide = "÷", clear = "C", negative = "±", percent = "%"
        
        var buttonColor: Color {
            switch self {
            case .clear, .negative, .percent: return .init(red: 0.2, green: 0.8, blue: 0.8)
            case .divide, .multiply, .subtract, .add, .equals: return .init(red: 1, green: 0.4, blue: 0.7)
            default: return .init(red: 0.3, green: 0.3, blue: 0.8)
            }
        }
    }
    
    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)
            
            VStack(spacing: 12) {
                Spacer()
                
                Text(calculator.displayValue)
                    .font(.system(size: 64, weight: .thin, design: .rounded))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity, alignment: .trailing)
                    .padding(.horizontal, 30)
                    .overlay(
                        Rectangle()
                            .stroke(Color.init(red: 0.3, green: 0.8, blue: 0.8), lineWidth: 2)
                            .blur(radius: 5)
                    )
                
                ForEach(buttons, id: \.self) { row in
                    HStack(spacing: 12) {
                        ForEach(row, id: \.self) { button in
                            NeonButton(title: button.rawValue,
                                      color: button.buttonColor) {
                                self.buttonTapped(button)
                            }
                            if button == .zero {
                                Spacer()
                            }
                        }
                    }
                }
            }
            .padding(.bottom, 30)
        }
    }
    
    private func buttonTapped(_ button: CalcButton) {
        switch button {
        case .clear:
            calculator.clear()
        case .equals:
            calculator.calculate()
        case .add, .subtract, .multiply, .divide:
            calculator.setOperation(button.rawValue)
        default:
            calculator.addDigit(button.rawValue)
        }
    }
}