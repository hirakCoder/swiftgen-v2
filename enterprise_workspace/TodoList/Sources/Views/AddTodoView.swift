import SwiftUI

struct AddTodoView: View {
    @EnvironmentObject var todoManager: TodoManager
    @Binding var isPresented: Bool
    @State private var title = ""
    @State private var priority: Todo.Priority = .medium
    @State private var includeDeadline = false
    @State private var deadline = Date()
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Task Details")) {
                    TextField("Task Title", text: $title)
                    
                    Picker("Priority", selection: $priority) {
                        ForEach(Todo.Priority.allCases, id: \.self) { priority in
                            Label(priority.rawValue.capitalized, systemImage: "flag.fill")
                                .foregroundColor(priority.color)
                                .tag(priority)
                        }
                    }
                }
                
                Section {
                    Toggle("Add Deadline", isOn: $includeDeadline)
                    if includeDeadline {
                        DatePicker("Deadline", selection: $deadline, displayedComponents: [.date])
                    }
                }
            }
            .navigationTitle("New Todo")
            .navigationBarItems(
                leading: Button("Cancel") {
                    dismiss()
                },
                trailing: Button("Add") {
                    let newTodo = Todo(
                        title: title,
                        priority: priority,
                        deadline: includeDeadline ? deadline : nil
                    )
                    todoManager.addTodo(newTodo)
                    dismiss()
                }
                .disabled(title.isEmpty)
            )
        }
    }
}