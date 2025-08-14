import SwiftUI

struct ContentView: View {
    @State private var diceValue = 1
    @State private var isRolling = false
    @State private var hapticEngine: CHHapticEngine?
    
    var body: some View {
        ZStack {
            LinearGradient(gradient: Gradient(colors: [.blue.opacity(0.3), .purple.opacity(0.3)]),
                          startPoint: .topLeading,
                          endPoint: .bottomTrailing)
                .ignoresSafeArea()
            
            VStack(spacing: 40) {
                DiceView(value: diceValue)
                    .frame(width: 200)
                    .padding()
                
                Button(action: rollDice) {
                    Text("Roll Dice")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                        .frame(width: 200, height: 60)
                        .background(Color.blue)
                        .cornerRadius(30)
                        .shadow(radius: 5)
                }
                .disabled(isRolling)
            }
        }
        .onAppear(perform: prepareHaptics)
    }
    
    private func rollDice() {
        isRolling = true
        withAnimation(.interpolatingSpring(stiffness: 100, damping: 5)) {
            diceValue = Int.random(in: 1...6)
        }
        
        playHaptics()
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            isRolling = false
        }
    }
    
    private func prepareHaptics() {
        guard CHHapticEngine.capabilitiesForHardware().supportsHaptics else { return }
        
        do {
            hapticEngine = try CHHapticEngine()
            try hapticEngine?.start()
        } catch {
            print("Haptics initialization failed: \(error)")
        }
    }
    
    private func playHaptics() {
        guard CHHapticEngine.capabilitiesForHardware().supportsHaptics,
              let engine = hapticEngine else { return }
        
        let intensity = CHHapticEventParameter(parameterID: .hapticIntensity, value: 1.0)
        let sharpness = CHHapticEventParameter(parameterID: .hapticSharpness, value: 1.0)
        let event = CHHapticEvent(eventType: .hapticTransient, parameters: [intensity, sharpness], relativeTime: 0)
        
        do {
            let pattern = try CHHapticPattern(events: [event], parameters: [])
            let player = try engine.makePlayer(with: pattern)
            try player.start(atTime: 0)
        } catch {
            print("Failed to play haptics: \(error)")
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}