import SwiftUI
import Combine

struct ContentView: View {
    @State private var timeRemaining = 60
    @State private var timerRunning = false
    let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            Color.black.opacity(0.8).edgesIgnoringSafeArea(.all)
            VStack {
                Text("\(timeRemaining) Seconds")
                    .font(.system(size: 60, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                    .padding()
                    .onReceive(timer) { _ in
                        if self.timerRunning && self.timeRemaining > 0 {
                            self.timeRemaining -= 1
                        }
                    }

                HStack {
                    Button(action: {
                        self.timerRunning = true
                    }) {
                        Text("Start")
                            .bold()
                            .foregroundColor(.green)
                            .padding()
                            .background(Circle().fill(Color.white))
                    }
                    Button(action: {
                        self.timerRunning = false
                    }) {
                        Text("Stop")
                            .bold()
                            .foregroundColor(.red)
                            .padding()
                            .background(Circle().fill(Color.white))
                    }
                    Button(action: {
                        self.timeRemaining = 60
                        self.timerRunning = false
                    }) {
                        Text("Reset")
                            .bold()
                            .foregroundColor(.blue)
                            .padding()
                            .background(Circle().fill(Color.white))
                    }
                }
            }
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}