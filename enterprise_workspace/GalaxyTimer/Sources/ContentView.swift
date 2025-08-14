import SwiftUI

struct ContentView: View {
    @State private var timeRemaining = 60
    let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()
    @Environment(\ .dismiss) var dismiss

    var body: some View {
        ZStack {
            LinearGradient(gradient: Gradient(colors: [Color.purple, Color.black]), startPoint: .top, endPoint: .bottom)
                .edgesIgnoringSafeArea(.all)
            VStack {
                Text(\"Galaxy Timer\")
                    .font(.largeTitle)
                    .foregroundColor(.white)
                    .padding()
                Text(\"\(timeRemaining) seconds\"
                    .font(.system(size: 60))
                    .foregroundColor(.white)
                    .onReceive(timer) { _ in
                        if timeRemaining > 0 {
                            timeRemaining -= 1
                        }
                    }
                Button(action: {
                    dismiss()
                }) {
                    Text(\"Dismiss\")
                        .foregroundColor(.purple)
                        .padding()
                        .background(Color.white)
                        .clipShape(Capsule())
                }
                .padding()
            }
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}