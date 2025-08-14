import SwiftUI

struct ContentView: View {
    @StateObject private var timerManager = TimerManager()
    @State private var showingMinutePicker = false
    
    var formattedTime: String {
        let minutes = Int(timerManager.timeRemaining) / 60
        let seconds = Int(timerManager.timeRemaining) % 60
        let deciseconds = Int((timerManager.timeRemaining.truncatingRemainder(dividingBy: 1)) * 10)
        return String(format: "%02d:%02d.%01d", minutes, seconds, deciseconds)
    }
    
    var progress: Double {
        let total = Double(timerManager.selectedMinutes * 60)
        return timerManager.timeRemaining / total
    }
    
    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)
            
            VStack(spacing: 30) {
                Text(formattedTime)
                    .font(.system(size: 64, weight: .thin, design: .monospaced))
                    .foregroundColor(.white)
                    .frame(height: 80)
                    .contentShape(Rectangle())
                    .onTapGesture {
                        if !timerManager.isRunning {
                            showingMinutePicker.toggle()
                        }
                    }
                
                ZStack {
                    CircularProgressView(progress: progress, color: .blue)
                        .frame(width: 250, height: 250)
                    
                    Button(action: {
                        if timerManager.isRunning {
                            timerManager.stopTimer()
                        } else {
                            timerManager.startTimer()
                        }
                    }) {
                        Circle()
                            .fill(timerManager.isRunning ? Color.red : Color.green)
                            .frame(width: 70, height: 70)
                            .overlay(
                                Image(systemName: timerManager.isRunning ? "pause.fill" : "play.fill")
                                    .foregroundColor(.white)
                                    .font(.title)
                            )
                    }
                }
                
                Button(action: {
                    timerManager.resetTimer()
                }) {
                    Text("Reset")
                        .foregroundColor(.white)
                        .padding(.horizontal, 30)
                        .padding(.vertical, 10)
                        .background(Capsule().stroke(Color.white, lineWidth: 1))
                }
            }
        }
        .sheet(isPresented: $showingMinutePicker) {
            NavigationView {
                Picker("Minutes", selection: $timerManager.selectedMinutes) {
                    ForEach(1...60, id: \.self) { minute in
                        Text("\(minute) minutes")
                    }
                }
                .pickerStyle(.wheel)
                .navigationTitle("Set Timer")
                .navigationBarItems(trailing: Button("Done") {
                    showingMinutePicker = false
                    timerManager.resetTimer()
                })
            }
        }
    }
}