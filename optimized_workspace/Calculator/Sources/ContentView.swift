import SwiftUI

struct ContentView: View {
    @StateObject private var model = CalculatorModel()
    
    let buttons: [[CalculatorButton.Config]] = [
        [.init(title: "AC", color: .gray, isWide: false),
         .init(title: "±", color: .gray, isWide: false),
         .init(title: "%", color: .gray, isWide: false),
         .init(title: "÷", color: .orange, isWide: false)],
        [.init(title: "7", color: .darkGray, isWide: false),
         .init(title: "8", color: .darkGray, isWide: false),
         .init(title: "9", color: .darkGray, isWide: false),
         .init(title: "×", color: .orange, isWide: false)],
        [.init(title: "4", color: .darkGray, isWide: false),
         .init(title: "5", color: .darkGray, isWide: false),
         .init(title: "6", color: .darkGray, isWide: false),
         .init(title: "−", color: .orange, isWide: false)],
        [.init(title: "1", color: .darkGray, isWide: false),
         .init(title: "2", color: .darkGray, isWide: false),
         .init(title: "3", color: .darkGray, isWide: false),
         .init(title: "+", color: .orange, isWide: false)],
        [.init(title: "0", color: .darkGray, isWide: true),
         .init(title: ".", color: .darkGray, isWide: false),
         .init(title: "=", color: .orange, isWide: false)]
    ]
    
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 12) {
                Spacer()
                
                HStack {
                    Spacer()
                    Text(model.display)
                        .font(.system(size: 64))
                        .foregroundColor(.white)
                        .minimumScaleFactor(0.5)
                        .lineLimit(1)
                        .padding(.horizontal, 24)
                }
                
                VStack(spacing: 12) {
                    ForEach(buttons, id: \.self) { row in
                        HStack(spacing: 12) {
                            ForEach(row, id: \.title) { config in
                                let width = (geometry.size.width - 60) / 4
                                CalculatorButton(
                                    title: config.title,
                                    color: config.color,
                                    width: config.isWide ? width * 2 + 12 : width
                                ) {
                                    handleButton(config.title)
                                }
                            }
                        }
                    }
                }
                .padding(.horizontal)
            }
            .padding(.bottom)
        }
        .background(Color.black.edgesIgnoringSafeArea(.all))
    }
    
    private func handleButton(_ title: String) {
        switch title {
        case "0"..."9", ".": model.addDigit(title)
        case "+": model.setOperation(.add)
        case "−": model.setOperation(.subtract)
        case "×": model.setOperation(.multiply)
        case "÷": model.setOperation(.divide)
        case "=": model.calculate()
        case "AC": model.clear()
        default: break
        }
    }
}

extension CalculatorButton {
    struct Config: Hashable {
        let title: String
        let color: Color
        let isWide: Bool
    }
}

extension View {
    func pressEvents(onPress: @escaping () -> Void, onRelease: @escaping () -> Void) -> some View {
        self.simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in onPress() }
                .onEnded { _ in onRelease() }
        )
    }
}

extension Color {
    static let darkGray = Color(white: 0.3)
}