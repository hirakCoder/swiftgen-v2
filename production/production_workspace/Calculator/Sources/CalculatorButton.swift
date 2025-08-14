import SwiftUI


struct CalculatorButton: View {
    let label: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            {'type': 'Text', 'text': 'label', 'modifiers': [('font', '.title'), ('frame', 'width: 70, height: 70'), ('background', '.gray.opacity(0.2)'), ('clipShape', 'Circle()')]}
        }
    }

}