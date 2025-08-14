import SwiftUI


struct TodoRowView: View {
    let todo: TodoItem
    
    var body: some View {
        HStack {
            Image(systemName: todo.isCompleted ? "checkmark.circle.fill" : "circle")
                .foregroundStyle(todo.isCompleted ? .green : .gray)
            Text("todo.text")
                .strikethrough(todo.isCompleted)
            Spacer()
        }
    }

}