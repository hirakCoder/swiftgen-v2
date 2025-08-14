import SwiftUI

struct ContentView: View {
    @State private var display = "0"
    @State private var currentOperation: Operation? = nil
    @State private var previousValue: Double? = nil
    
    let buttons: [[CalculatorButton]] = [
        [.init(label: "AC", type: .function), .init(label: "±", type: .function), .init(label: "%", type: .function), .init(label: "/", type: .operation)],
        [.init(label: "7"), .init(label: "8"), .init(label: "9"), .init(label: "*", type: .operation)],
        [.init(label: "4"), .init(label: "5"), .init(label: "6"), .init(label: "-", type: .operation)],
        [.init(label: "1"), .init(label: "2"), .init(label: "3"), .init(label: "+", type: .operation)],
        [.init(label: "0", widthMultiplier: 2), .init(label: "."), .init(label: "=", type: .operation)]
    ]
    
    var body: some View {
        VStack(spacing: 10) {
            Spacer()
            Text(display)
                .font(.largeTitle)
                .padding()
            ForEach(buttons, id: \Self.self) { row in
                HStack(spacing: 10) {
                    ForEach(row) { button in
                        Button(action: { self.buttonTapped(button) }) {
                            Text(button.label)
                                .frame(width: self.buttonWidth(button), height: self.buttonHeight())
                                .background(button.type.backgroundColor)
                                .foregroundColor(.white)
                                .font(.title)
                                .cornerRadius(self.buttonHeight() / 2)
                        }
                    }
                }
            }
        }
        .padding()
    }
    
    private func buttonWidth(_ button: CalculatorButton) -> CGFloat {
        let screenWidth = UIScreen.main.bounds.width - 40 // Padding
        let width = (screenWidth - 30) / 4 // 3 spaces, 4 buttons
        return button.widthMultiplier * width
    }
    
    private func buttonHeight() -> CGFloat {
        return (UIScreen.main.bounds.width - 40 - 30) / 4
    }
    
    private func buttonTapped(_ button: CalculatorButton) {
        switch button.type {
        case .digit, .decimal:
            if display == "0" || currentOperation != nil {
                display = button.label
            } else {
                display += button.label
            }
        case .function:
            handleFunction(button.label)
        case .operation:
            handleOperation(button.type)
        }
    }
    
    private func handleFunction(_ function: String) {
        // Implement function handling
    }
    
    private func handleOperation(_ operation: CalculatorButton.ButtonType) {
        // Implement operation handling
    }
}

struct CalculatorButton: Identifiable {
    let id = UUID()
    let label: String
    var type: ButtonType = .digit
    var widthMultiplier: CGFloat = 1
    
    enum ButtonType {
        case digit, function, operation, decimal
        
        var backgroundColor: Color {
            switch self {
            case .function, .operation:
                return .blue
            default:
                return .gray
            }
        }
    }
    
    init(label: String, type: ButtonType = .digit, widthMultiplier: CGFloat = 1) {
        self.label = label
        self.type = type
        self.widthMultiplier = widthMultiplier
    }
}