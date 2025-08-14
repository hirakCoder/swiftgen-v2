import SwiftUI
import Combine

@MainActor
final class TodoViewModelViewModel: ObservableObject {
    @Published var todos: [TodoItem] = []
    @Published var newTodoText: String = ""
    
    func addTodo() {
        if !newTodoText.isEmpty {
                    let todo = TodoItem(id: UUID(), text: newTodoText, isCompleted: false)
                    todos.append(todo)
                    newTodoText = ""
                }
    }
    func toggleTodo(id: UUID) {
        if let index = todos.firstIndex(where: { $0.id == id }) {
                    todos[index].isCompleted.toggle()
                }
    }
    func deleteTodo(id: UUID) {
        todos.removeAll { $0.id == id }
    }
}