import Foundation

struct Todo: Identifiable, Codable {
    let id: UUID
    var title: String
    var isCompleted: Bool
    var priority: Priority
    var deadline: Date?
    
    enum Priority: String, Codable, CaseIterable {
        case low, medium, high
        
        var color: Color {
            switch self {
            case .low: return .green
            case .medium: return .orange
            case .high: return .red
            }
        }
    }
    
    init(id: UUID = UUID(), title: String, isCompleted: Bool = false, priority: Priority = .medium, deadline: Date? = nil) {
        self.id = id
        self.title = title
        self.isCompleted = isCompleted
        self.priority = priority
        self.deadline = deadline
    }
}