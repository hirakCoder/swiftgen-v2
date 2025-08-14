import SwiftUI

struct ContentView: View {
    @EnvironmentObject var todoManager: TodoManager
    @State private var showingAddTodo = false
    @State private var newTodoTitle = ""
    @State private var selectedPriority: Todo.Priority = .medium
    @State private var selectedDeadline: Date = Date()
    @State private var includeDeadline = false
    
    var body: some View {
        NavigationView {
            List {
                ForEach(todoManager.todos) { todo in
                    TodoRowView(todo: todo)
                        .swipeActions(edge: .trailing) {
                            Button(role: .destructive) {
                                if let index = todoManager.todos.firstIndex(where: { $0.id == todo.id }) {
                                    todoManager.removeTodo(at: IndexSet(integer: index))
                                }
                            } label: {
                                Label("Delete", systemImage: "trash")
                            }
                        }
                }
            }
            .navigationTitle("Todo List")
            .toolbar {
                Button {
                    showingAddTodo = true
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.title2)
                }
            }
            .sheet(isPresented: $showingAddTodo) {
                AddTodoView(isPresented: $showingAddTodo)
            }
        }
    }
}