import SwiftUI
import Combine

@MainActor
final class AppViewModelViewModel: ObservableObject {
    @Published var state: String = ""
    

}