import Foundation

struct TodoItem: Identifiable {
    let id: UUID
    var text: String
    var isCompleted: Bool
}