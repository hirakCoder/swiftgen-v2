@main
struct TicTacToeApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

import SwiftUI
import Combine

class GameState: ObservableObject {
    @Published var board = Array(repeating: "", count: 9)
    @Published var currentPlayer = "X"
    @Published var winner: String? = nil
    @Published var winningCombination: Set<Int> = []
    @Published var isGameOver = false
    
    func makeMove(at index: Int) {
        guard board[index].isEmpty && winner == nil else { return }
        
        board[index] = currentPlayer
        checkWinner()
        if winner == nil {
            currentPlayer = currentPlayer == "X" ? "O" : "X"
        }
    }
    
    func checkWinner() {
        let winPatterns = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8], // Columns
            [0, 4, 8], [2, 4, 6]             // Diagonals
        ]
        
        for pattern in winPatterns {
            if pattern.map({ board[$0] }).allSatisfy({ $0 == currentPlayer }) {
                winner = currentPlayer
                winningCombination = Set(pattern)
                isGameOver = true
                return
            }
        }
        
        if board.allSatisfy({ !$0.isEmpty }) {
            winner = "Draw"
            isGameOver = true
        }
    }
    
    func resetGame() {
        board = Array(repeating: "", count: 9)
        currentPlayer = "X"
        winner = nil
        winningCombination = []
        isGameOver = false
    }
}