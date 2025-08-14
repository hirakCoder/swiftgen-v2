"""
Template Fallback System - Guaranteed working templates for common app types
When LLM generation fails, fall back to these tested templates
"""

import json
from typing import Dict, List, Optional
import re

class TemplateFallbackSystem:
    """
    Provides working templates for common app types
    These are guaranteed to compile and run
    """
    
    @staticmethod
    def get_template(app_type: str, app_name: str) -> Optional[Dict]:
        """
        Get a working template for the given app type
        Returns None if no template available
        """
        app_type_lower = app_type.lower()
        
        # Detect app type from description
        if any(word in app_type_lower for word in ['timer', 'stopwatch', 'countdown']):
            return TemplateFallbackSystem._get_timer_template(app_name)
        elif any(word in app_type_lower for word in ['counter', 'increment', 'decrement', 'tally']):
            return TemplateFallbackSystem._get_counter_template(app_name)
        elif any(word in app_type_lower for word in ['calculator', 'calculate', 'math']):
            return TemplateFallbackSystem._get_calculator_template(app_name)
        elif any(word in app_type_lower for word in ['todo', 'task', 'checklist']):
            return TemplateFallbackSystem._get_todo_template(app_name)
        elif any(word in app_type_lower for word in ['weather', 'forecast', 'temperature']):
            return TemplateFallbackSystem._get_weather_template(app_name)
        elif any(word in app_type_lower for word in ['note', 'memo', 'journal']):
            return TemplateFallbackSystem._get_notes_template(app_name)
        elif any(word in app_type_lower for word in ['dice', 'roll', 'random']):
            return TemplateFallbackSystem._get_dice_template(app_name)
        
        return None
    
    @staticmethod
    def _get_timer_template(app_name: str) -> Dict:
        """Working timer app template"""
        return {
            "files": [
                {
                    "path": "Sources/App.swift",
                    "content": f"""import SwiftUI

@main
struct {app_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}"""
                },
                {
                    "path": "Sources/ContentView.swift",
                    "content": """import SwiftUI
import Combine

struct ContentView: View {
    @StateObject private var viewModel = TimerViewModel()
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 30) {
                Text(viewModel.timeString)
                    .font(.system(size: 60, weight: .thin, design: .monospaced))
                    .padding()
                
                HStack(spacing: 20) {
                    Button(action: {
                        if viewModel.isRunning {
                            viewModel.stop()
                        } else {
                            viewModel.start()
                        }
                    }) {
                        Text(viewModel.isRunning ? "Stop" : "Start")
                            .font(.title2)
                            .frame(width: 100, height: 50)
                            .background(viewModel.isRunning ? Color.red : Color.green)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                    }
                    
                    Button(action: {
                        viewModel.reset()
                    }) {
                        Text("Reset")
                            .font(.title2)
                            .frame(width: 100, height: 50)
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                    }
                }
            }
            .padding()
            .navigationTitle("Timer")
        }
    }
}

@MainActor
class TimerViewModel: ObservableObject {
    @Published var seconds: Int = 0
    @Published var isRunning: Bool = false
    
    private var cancellable: AnyCancellable?
    
    var timeString: String {
        let hours = seconds / 3600
        let minutes = (seconds % 3600) / 60
        let secs = seconds % 60
        return String(format: "%02d:%02d:%02d", hours, minutes, secs)
    }
    
    func start() {
        isRunning = true
        cancellable = Timer.publish(every: 1, on: .main, in: .common)
            .autoconnect()
            .sink { _ in
                self.seconds += 1
            }
    }
    
    func stop() {
        isRunning = false
        cancellable?.cancel()
    }
    
    func reset() {
        stop()
        seconds = 0
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}"""
                }
            ]
        }
    
    @staticmethod
    def _get_counter_template(app_name: str) -> Dict:
        """Working counter app template"""
        return {
            "files": [
                {
                    "path": "Sources/App.swift",
                    "content": f"""import SwiftUI

@main
struct {app_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}"""
                },
                {
                    "path": "Sources/ContentView.swift",
                    "content": """import SwiftUI

struct ContentView: View {
    @State private var count = 0
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 30) {
                Text("\\(count)")
                    .font(.system(size: 80, weight: .bold))
                    .foregroundColor(.primary)
                
                HStack(spacing: 20) {
                    Button(action: {
                        count -= 1
                    }) {
                        Image(systemName: "minus.circle.fill")
                            .font(.system(size: 50))
                            .foregroundColor(.red)
                    }
                    
                    Button(action: {
                        count += 1
                    }) {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 50))
                            .foregroundColor(.green)
                    }
                }
                
                Button(action: {
                    count = 0
                }) {
                    Text("Reset")
                        .font(.title2)
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
            }
            .padding()
            .navigationTitle("Counter")
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}"""
                }
            ]
        }
    
    @staticmethod
    def _get_calculator_template(app_name: str) -> Dict:
        """Working calculator app template"""
        return {
            "files": [
                {
                    "path": "Sources/App.swift",
                    "content": f"""import SwiftUI

@main
struct {app_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}"""
                },
                {
                    "path": "Sources/ContentView.swift",
                    "content": """import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = CalculatorViewModel()
    
    let buttons: [[String]] = [
        ["C", "+/-", "%", "/"],
        ["7", "8", "9", "X"],
        ["4", "5", "6", "-"],
        ["1", "2", "3", "+"],
        ["0", ".", "="]
    ]
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 10) {
                Spacer()
                
                Text(viewModel.display)
                    .font(.system(size: 70))
                    .frame(maxWidth: .infinity, alignment: .trailing)
                    .padding()
                
                ForEach(buttons, id: \\.self) { row in
                    HStack(spacing: 10) {
                        ForEach(row, id: \\.self) { button in
                            Button(action: {
                                viewModel.buttonTapped(button)
                            }) {
                                Text(button)
                                    .font(.title)
                                    .frame(width: buttonWidth(button), height: 80)
                                    .background(buttonColor(button))
                                    .foregroundColor(.white)
                                    .cornerRadius(40)
                            }
                        }
                    }
                }
            }
            .padding()
            .navigationTitle("Calculator")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
    
    func buttonWidth(_ button: String) -> CGFloat {
        if button == "0" {
            return 170
        }
        return 80
    }
    
    func buttonColor(_ button: String) -> Color {
        if button == "=" {
            return .orange
        } else if "0123456789.".contains(button) {
            return .gray
        } else {
            return .blue
        }
    }
}

@MainActor
class CalculatorViewModel: ObservableObject {
    @Published var display = "0"
    
    private var currentNumber = 0.0
    private var previousNumber = 0.0
    private var operation = ""
    private var shouldResetDisplay = false
    
    func buttonTapped(_ button: String) {
        switch button {
        case "0"..."9":
            if shouldResetDisplay {
                display = button
                shouldResetDisplay = false
            } else {
                display = display == "0" ? button : display + button
            }
        case ".":
            if !display.contains(".") {
                display += "."
            }
        case "C":
            display = "0"
            currentNumber = 0
            previousNumber = 0
            operation = ""
        case "+", "-", "X", "/":
            operation = button
            previousNumber = Double(display) ?? 0
            shouldResetDisplay = true
        case "=":
            currentNumber = Double(display) ?? 0
            switch operation {
            case "+":
                display = String(previousNumber + currentNumber)
            case "-":
                display = String(previousNumber - currentNumber)
            case "X":
                display = String(previousNumber * currentNumber)
            case "/":
                display = previousNumber != 0 ? String(previousNumber / currentNumber) : "Error"
            default:
                break
            }
            shouldResetDisplay = true
        case "+/-":
            if let value = Double(display) {
                display = String(-value)
            }
        case "%":
            if let value = Double(display) {
                display = String(value / 100)
            }
        default:
            break
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}"""
                }
            ]
        }
    
    @staticmethod
    def _get_todo_template(app_name: str) -> Dict:
        """Working todo app template"""
        return {
            "files": [
                {
                    "path": "Sources/App.swift",
                    "content": f"""import SwiftUI

@main
struct {app_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}"""
                },
                {
                    "path": "Sources/ContentView.swift",
                    "content": """import SwiftUI

struct ContentView: View {
    @State private var todos: [TodoItem] = []
    @State private var newTodoText = ""
    @State private var showingAddSheet = false
    
    var body: some View {
        NavigationStack {
            List {
                ForEach(todos) { todo in
                    HStack {
                        Button(action: {
                            toggleTodo(todo)
                        }) {
                            Image(systemName: todo.isCompleted ? "checkmark.circle.fill" : "circle")
                                .foregroundColor(todo.isCompleted ? .green : .gray)
                        }
                        
                        Text(todo.title)
                            .strikethrough(todo.isCompleted)
                            .foregroundColor(todo.isCompleted ? .gray : .primary)
                        
                        Spacer()
                    }
                    .padding(.vertical, 4)
                }
                .onDelete(perform: deleteTodos)
            }
            .navigationTitle("Todo List")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingAddSheet = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddSheet) {
                AddTodoView(todos: $todos, isPresented: $showingAddSheet)
            }
        }
    }
    
    func toggleTodo(_ todo: TodoItem) {
        if let index = todos.firstIndex(where: { $0.id == todo.id }) {
            todos[index].isCompleted.toggle()
        }
    }
    
    func deleteTodos(at offsets: IndexSet) {
        todos.remove(atOffsets: offsets)
    }
}

struct TodoItem: Identifiable {
    let id = UUID()
    let title: String
    var isCompleted: Bool = false
}

struct AddTodoView: View {
    @Binding var todos: [TodoItem]
    @Binding var isPresented: Bool
    @State private var todoText = ""
    
    var body: some View {
        NavigationStack {
            Form {
                TextField("Enter todo", text: $todoText)
            }
            .navigationTitle("Add Todo")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        isPresented = false
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Add") {
                        if !todoText.isEmpty {
                            todos.append(TodoItem(title: todoText))
                            isPresented = false
                        }
                    }
                    .disabled(todoText.isEmpty)
                }
            }
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}"""
                }
            ]
        }
    
    @staticmethod
    def _get_weather_template(app_name: str) -> Dict:
        """Working weather app template with mock data"""
        return {
            "files": [
                {
                    "path": "Sources/App.swift",
                    "content": f"""import SwiftUI

@main
struct {app_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}"""
                },
                {
                    "path": "Sources/ContentView.swift",
                    "content": """import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = WeatherViewModel()
    
    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(gradient: Gradient(colors: [.blue, .white]), 
                              startPoint: .topLeading, 
                              endPoint: .bottomTrailing)
                    .ignoresSafeArea()
                
                VStack(spacing: 20) {
                    Text(viewModel.cityName)
                        .font(.largeTitle)
                        .foregroundColor(.white)
                    
                    VStack(spacing: 10) {
                        Image(systemName: viewModel.weatherIcon)
                            .font(.system(size: 100))
                            .foregroundColor(.white)
                        
                        Text("\\(viewModel.temperature)°")
                            .font(.system(size: 70))
                            .foregroundColor(.white)
                        
                        Text(viewModel.description)
                            .font(.title)
                            .foregroundColor(.white)
                    }
                    
                    HStack(spacing: 40) {
                        WeatherDetailView(icon: "wind", value: "\\(viewModel.windSpeed) mph", label: "Wind")
                        WeatherDetailView(icon: "humidity", value: "\\(viewModel.humidity)%", label: "Humidity")
                    }
                    
                    Spacer()
                    
                    Button(action: {
                        viewModel.refreshWeather()
                    }) {
                        Text("Refresh")
                            .font(.title2)
                            .padding()
                            .background(Color.white.opacity(0.3))
                            .foregroundColor(.white)
                            .cornerRadius(10)
                    }
                }
                .padding()
            }
            .navigationBarHidden(true)
        }
    }
}

struct WeatherDetailView: View {
    let icon: String
    let value: String
    let label: String
    
    var body: some View {
        VStack {
            Image(systemName: icon)
                .font(.title)
                .foregroundColor(.white)
            Text(value)
                .font(.title2)
                .foregroundColor(.white)
            Text(label)
                .font(.caption)
                .foregroundColor(.white)
        }
    }
}

@MainActor
class WeatherViewModel: ObservableObject {
    @Published var cityName = "San Francisco"
    @Published var temperature = 72
    @Published var description = "Partly Cloudy"
    @Published var weatherIcon = "cloud.sun.fill"
    @Published var windSpeed = 8
    @Published var humidity = 65
    
    private let mockWeatherData = [
        (temp: 72, desc: "Partly Cloudy", icon: "cloud.sun.fill", wind: 8, humidity: 65),
        (temp: 68, desc: "Cloudy", icon: "cloud.fill", wind: 12, humidity: 70),
        (temp: 75, desc: "Sunny", icon: "sun.max.fill", wind: 5, humidity: 55),
        (temp: 65, desc: "Rainy", icon: "cloud.rain.fill", wind: 15, humidity: 85),
        (temp: 70, desc: "Clear", icon: "sun.min.fill", wind: 6, humidity: 60)
    ]
    
    func refreshWeather() {
        // Simulate weather refresh with mock data
        let randomWeather = mockWeatherData.randomElement()!
        temperature = randomWeather.temp
        description = randomWeather.desc
        weatherIcon = randomWeather.icon
        windSpeed = randomWeather.wind
        humidity = randomWeather.humidity
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}"""
                }
            ]
        }
    
    @staticmethod
    def _get_notes_template(app_name: str) -> Dict:
        """Working notes app template"""
        return {
            "files": [
                {
                    "path": "Sources/App.swift",
                    "content": f"""import SwiftUI

@main
struct {app_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}"""
                },
                {
                    "path": "Sources/ContentView.swift",
                    "content": """import SwiftUI

struct ContentView: View {
    @State private var notes: [Note] = []
    @State private var searchText = ""
    @State private var showingAddNote = false
    @State private var selectedNote: Note?
    
    var filteredNotes: [Note] {
        if searchText.isEmpty {
            return notes
        } else {
            return notes.filter { $0.title.localizedCaseInsensitiveContains(searchText) || 
                                 $0.content.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
    var body: some View {
        NavigationStack {
            List {
                ForEach(filteredNotes) { note in
                    NavigationLink(destination: NoteDetailView(note: binding(for: note))) {
                        VStack(alignment: .leading) {
                            Text(note.title)
                                .font(.headline)
                            Text(note.content)
                                .font(.caption)
                                .lineLimit(2)
                                .foregroundColor(.secondary)
                        }
                        .padding(.vertical, 4)
                    }
                }
                .onDelete(perform: deleteNotes)
            }
            .searchable(text: $searchText)
            .navigationTitle("Notes")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        let newNote = Note(title: "New Note", content: "")
                        notes.append(newNote)
                        selectedNote = newNote
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
        }
    }
    
    func binding(for note: Note) -> Binding<Note> {
        guard let index = notes.firstIndex(where: { $0.id == note.id }) else {
            fatalError("Note not found")
        }
        return $notes[index]
    }
    
    func deleteNotes(at offsets: IndexSet) {
        notes.remove(atOffsets: offsets)
    }
}

struct Note: Identifiable {
    let id = UUID()
    var title: String
    var content: String
    var date = Date()
}

struct NoteDetailView: View {
    @Binding var note: Note
    
    var body: some View {
        VStack(alignment: .leading) {
            TextField("Title", text: $note.title)
                .font(.largeTitle)
                .padding(.horizontal)
            
            TextEditor(text: $note.content)
                .padding(.horizontal)
            
            Spacer()
        }
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}"""
                }
            ]
        }
    
    @staticmethod
    def _get_dice_template(app_name: str) -> Dict:
        """Working dice roller app template"""
        return {
            "files": [
                {
                    "path": "Sources/App.swift",
                    "content": f"""import SwiftUI

@main
struct {app_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}"""
                },
                {
                    "path": "Sources/ContentView.swift",
                    "content": """import SwiftUI

struct ContentView: View {
    @State private var diceValue = 1
    @State private var isRolling = false
    @State private var rotation = 0.0
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 40) {
                Spacer()
                
                ZStack {
                    RoundedRectangle(cornerRadius: 20)
                        .fill(Color.white)
                        .frame(width: 150, height: 150)
                        .shadow(radius: 10)
                    
                    Text("\\(diceValue)")
                        .font(.system(size: 80, weight: .bold))
                }
                .rotation3DEffect(.degrees(rotation), axis: (x: 1, y: 1, z: 0))
                .animation(.spring(), value: rotation)
                
                Button(action: rollDice) {
                    Text("Roll Dice")
                        .font(.title)
                        .padding()
                        .frame(width: 200, height: 60)
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(15)
                }
                .disabled(isRolling)
                
                Spacer()
            }
            .padding()
            .navigationTitle("Dice Roller")
        }
    }
    
    func rollDice() {
        isRolling = true
        rotation += 360
        
        // Simulate rolling animation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            diceValue = Int.random(in: 1...6)
            isRolling = false
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}"""
                }
            ]
        }
    
    @staticmethod
    def detect_app_type(description: str) -> str:
        """Detect app type from description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['timer', 'stopwatch', 'countdown']):
            return "timer"
        elif any(word in description_lower for word in ['counter', 'increment', 'decrement', 'tally']):
            return "counter"
        elif any(word in description_lower for word in ['calculator', 'calculate', 'math']):
            return "calculator"
        elif any(word in description_lower for word in ['todo', 'task', 'checklist']):
            return "todo"
        elif any(word in description_lower for word in ['weather', 'forecast', 'temperature']):
            return "weather"
        elif any(word in description_lower for word in ['note', 'memo', 'journal']):
            return "notes"
        elif any(word in description_lower for word in ['dice', 'roll', 'random']):
            return "dice"
        
        return "unknown"