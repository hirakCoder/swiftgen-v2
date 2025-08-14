@main
struct DiceRollerApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}


import SwiftUI

struct DiceView: View {
    let value: Int
    @State private var rotation: Double = 0
    
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 16)
                .fill(Color.white)
                .shadow(radius: 8)
            
            GeometryReader { geometry in
                ForEach(0..<getDotCount(for: value), id: \.self) { index in
                    Circle()
                        .fill(Color.black)
                        .frame(width: geometry.size.width * 0.15)
                        .position(getDotPosition(index: index, in: geometry.size, for: value))
                }
            }
        }
        .aspectRatio(1, contentMode: .fit)
        .rotation3DEffect(Angle(degrees: rotation), axis: (x: 1, y: 1, z: 0))
    }
    
    private func getDotCount(for value: Int) -> Int {
        return value
    }
    
    private func getDotPosition(index: Int, in size: CGSize, for value: Int) -> CGPoint {
        let positions: [[[CGFloat]]] = [
            [[0.5, 0.5]],  // 1
            [[0.25, 0.25], [0.75, 0.75]],  // 2
            [[0.25, 0.25], [0.5, 0.5], [0.75, 0.75]],  // 3
            [[0.25, 0.25], [0.75, 0.25], [0.25, 0.75], [0.75, 0.75]],  // 4
            [[0.25, 0.25], [0.75, 0.25], [0.5, 0.5], [0.25, 0.75], [0.75, 0.75]],  // 5
            [[0.25, 0.25], [0.75, 0.25], [0.25, 0.5], [0.75, 0.5], [0.25, 0.75], [0.75, 0.75]]  // 6
        ]
        
        let position = positions[value - 1][index]
        return CGPoint(x: size.width * position[0], y: size.height * position[1])
    }
}