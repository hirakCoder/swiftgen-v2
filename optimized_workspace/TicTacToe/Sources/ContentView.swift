import SwiftUI

struct ContentView: View {
    @StateObject private var gameState = GameState()
    private let gridSpacing: CGFloat = 2
    private let animationDuration: Double = 0.3
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Tic Tac Toe")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Text(gameState.winner == nil ? "\(gameState.currentPlayer)'s Turn" : 
                    gameState.winner == "Draw" ? "It's a Draw!" : "\(gameState.winner!) Wins!")
                .font(.title2)
                .foregroundColor(gameState.winner == nil ? .primary : .blue)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: gridSpacing), count: 3), spacing: gridSpacing) {
                ForEach(0..<9) { index in
                    CellView(symbol: gameState.board[index],
                            isWinning: gameState.winningCombination.contains(index))
                        .onTapGesture {
                            withAnimation(.easeInOut(duration: animationDuration)) {
                                gameState.makeMove(at: index)
                            }
                        }
                }
            }
            .padding()
            .background(Color.gray.opacity(0.2))
            .cornerRadius(10)
            
            if gameState.isGameOver {
                Button("Play Again") {
                    withAnimation(.easeInOut(duration: animationDuration)) {
                        gameState.resetGame()
                    }
                }
                .font(.title3)
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(10)
            }
        }
        .padding()
    }
}

struct CellView: View {
    let symbol: String
    let isWinning: Bool
    
    var body: some View {
        ZStack {
            Rectangle()
                .fill(Color.white)
                .aspectRatio(1, contentMode: .fit)
                .shadow(radius: 2)
            
            Text(symbol)
                .font(.system(size: 50, weight: .bold))
                .foregroundColor(symbolColor)
                .scaleEffect(symbol.isEmpty ? 0 : 1)
                .animation(.spring(), value: symbol)
        }
        .background(isWinning ? Color.green.opacity(0.3) : Color.clear)
    }
    
    private var symbolColor: Color {
        switch symbol {
        case "X": return .red
        case "O": return .blue
        default: return .clear
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}