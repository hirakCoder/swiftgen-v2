import SwiftUI
import Combine

class TodoManager: ObservableObject {
    @Published var todos: [Todo] = []
    private let saveKey = "todos"
    
    init() {
        loadTodos()
    }
    
    func addTodo(_ todo: Todo) {
        todos.append(todo)
        saveTodos()
    }
    
    func removeTodo(at indexSet: IndexSet) {
        todos.remove(atOffsets: indexSet)
        saveTodos()
    }
    
    func toggleCompletion(for todo: Todo) {
        if let index = todos.firstIndex(where: { $0.id == todo.id }) {
            todos[index].isCompleted.toggle()
            saveTodos()
        }
    }
    
    private func saveTodos() {
        if let encoded = try? JSONEncoder().encode(todos) {
            UserDefaults.standard.set(encoded, forKey: saveKey)
        }
    }
    
    private func loadTodos() {
        if let data = UserDefaults.standard.data(forKey: saveKey),
           let decoded = try? JSONDecoder().decode([Todo].self, from: data) {
            todos = decoded
        }
    }
}