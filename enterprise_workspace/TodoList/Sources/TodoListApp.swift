import SwiftUI

@main
struct TodoListApp: App {
    @StateObject private var todoManager = TodoManager()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(todoManager)
        }
    }
}