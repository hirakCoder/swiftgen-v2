"""
Simple App Generator for SwiftGen V2
Generates iOS apps using flexible intent-based approach
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AppTemplate:
    """Represents an app template"""
    name: str
    files: Dict[str, str]
    
class SimpleAppGenerator:
    """
    Generates simple iOS apps based on intent
    No rigid templates - just flexible generation
    """
    
    def __init__(self):
        self.workspace_base = "workspaces"
    
    async def generate_app(
        self,
        intent: str,
        features: List[str],
        project_path: str
    ) -> Dict:
        """
        Generate app based on intent and features
        """
        try:
            # Create workspace directory
            os.makedirs(project_path, exist_ok=True)
            sources_dir = os.path.join(project_path, "Sources")
            os.makedirs(sources_dir, exist_ok=True)
            
            # Extract app name from project path
            app_name = os.path.basename(project_path).title().replace('_', '')
            
            # Generate main app file
            app_swift = self._generate_app_file(app_name)
            with open(os.path.join(sources_dir, f"{app_name}App.swift"), 'w') as f:
                f.write(app_swift)
            
            # Generate content view based on intent
            content_view = self._generate_content_view(intent, features, app_name)
            with open(os.path.join(sources_dir, "ContentView.swift"), 'w') as f:
                f.write(content_view)
            
            return {
                'success': True,
                'files': {
                    f'{app_name}App.swift': app_swift,
                    'ContentView.swift': content_view
                },
                'message': f'Generated {app_name} app'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_app_file(self, app_name: str) -> str:
        """Generate the main app file"""
        return f"""import SwiftUI

@main
struct {app_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}"""
    
    def _generate_content_view(self, intent: str, features: List[str], app_name: str) -> str:
        """
        Generate content view based on intent
        This is where we interpret what the user wants
        """
        intent_lower = intent.lower()
        
        # Detect app type from intent
        if any(word in intent_lower for word in ['counter', 'count', 'increment', 'decrement']):
            return self._counter_view()
        elif any(word in intent_lower for word in ['timer', 'stopwatch', 'clock', 'time']):
            return self._timer_view()
        elif any(word in intent_lower for word in ['todo', 'task', 'list', 'checklist']):
            return self._todo_view()
        elif any(word in intent_lower for word in ['calculator', 'calculate', 'math']):
            return self._calculator_view()
        elif any(word in intent_lower for word in ['weather', 'temperature', 'forecast']):
            return self._weather_view()
        elif any(word in intent_lower for word in ['note', 'notes', 'memo']):
            return self._notes_view()
        else:
            # Default to a simple app with the requested features
            return self._default_view(app_name, features)
    
    def _counter_view(self) -> str:
        """Generate a counter app view"""
        return """import SwiftUI

struct ContentView: View {
    @State private var count = 0
    
    var body: some View {
        VStack(spacing: 30) {
            Text("Counter")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Text("\\(count)")
                .font(.system(size: 72, weight: .medium, design: .rounded))
                .foregroundColor(.blue)
            
            HStack(spacing: 20) {
                Button(action: { count -= 1 }) {
                    Image(systemName: "minus.circle.fill")
                        .font(.system(size: 44))
                        .foregroundColor(.red)
                }
                
                Button(action: { count = 0 }) {
                    Text("Reset")
                        .font(.title2)
                        .padding()
                        .background(Color.gray.opacity(0.2))
                        .cornerRadius(10)
                }
                
                Button(action: { count += 1 }) {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 44))
                        .foregroundColor(.green)
                }
            }
        }
        .padding()
    }
}"""
    
    def _timer_view(self) -> str:
        """Generate a timer app view"""
        return """import SwiftUI
import Foundation

struct ContentView: View {
    @State private var timeElapsed = 0
    @State private var isRunning = false
    @State private var timer: Timer?
    
    var formattedTime: String {
        let minutes = timeElapsed / 60
        let seconds = timeElapsed % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }
    
    var body: some View {
        VStack(spacing: 30) {
            Text("Timer")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Text(formattedTime)
                .font(.system(size: 60, weight: .medium, design: .monospaced))
                .foregroundColor(.blue)
            
            HStack(spacing: 20) {
                Button(action: toggleTimer) {
                    Image(systemName: isRunning ? "pause.circle.fill" : "play.circle.fill")
                        .font(.system(size: 44))
                        .foregroundColor(isRunning ? .orange : .green)
                }
                
                Button(action: resetTimer) {
                    Image(systemName: "arrow.clockwise.circle.fill")
                        .font(.system(size: 44))
                        .foregroundColor(.red)
                }
            }
        }
        .padding()
    }
    
    func toggleTimer() {
        if isRunning {
            timer?.invalidate()
            timer = nil
        } else {
            timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { _ in
                timeElapsed += 1
            }
        }
        isRunning.toggle()
    }
    
    func resetTimer() {
        timer?.invalidate()
        timer = nil
        timeElapsed = 0
        isRunning = false
    }
}"""
    
    def _todo_view(self) -> str:
        """Generate a todo list app view"""
        return """import SwiftUI

struct TodoItem: Identifiable {
    let id = UUID()
    var title: String
    var isCompleted: Bool = false
}

struct ContentView: View {
    @State private var todos: [TodoItem] = []
    @State private var newTodoText = ""
    
    var body: some View {
        NavigationView {
            VStack {
                HStack {
                    TextField("Add new task", text: $newTodoText)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                    
                    Button(action: addTodo) {
                        Image(systemName: "plus.circle.fill")
                            .font(.title)
                            .foregroundColor(.blue)
                    }
                    .disabled(newTodoText.isEmpty)
                }
                .padding()
                
                List {
                    ForEach(todos) { todo in
                        HStack {
                            Image(systemName: todo.isCompleted ? "checkmark.circle.fill" : "circle")
                                .foregroundColor(todo.isCompleted ? .green : .gray)
                                .onTapGesture {
                                    toggleTodo(todo)
                                }
                            
                            Text(todo.title)
                                .strikethrough(todo.isCompleted)
                            
                            Spacer()
                        }
                    }
                    .onDelete(perform: deleteTodos)
                }
            }
            .navigationTitle("Todo List")
        }
    }
    
    func addTodo() {
        todos.append(TodoItem(title: newTodoText))
        newTodoText = ""
    }
    
    func toggleTodo(_ todo: TodoItem) {
        if let index = todos.firstIndex(where: { $0.id == todo.id }) {
            todos[index].isCompleted.toggle()
        }
    }
    
    func deleteTodos(at offsets: IndexSet) {
        todos.remove(atOffsets: offsets)
    }
}"""
    
    def _calculator_view(self) -> str:
        """Generate a calculator app view"""
        return """import SwiftUI

struct ContentView: View {
    @State private var display = "0"
    @State private var currentNumber = 0.0
    @State private var previousNumber = 0.0
    @State private var operation = ""
    
    let buttons = [
        ["C", "+/-", "%", "/"],
        ["7", "8", "9", "×"],
        ["4", "5", "6", "-"],
        ["1", "2", "3", "+"],
        ["0", ".", "="]
    ]
    
    var body: some View {
        VStack(spacing: 10) {
            Text(display)
                .font(.system(size: 64))
                .frame(maxWidth: .infinity, alignment: .trailing)
                .padding()
            
            ForEach(buttons, id: \\.self) { row in
                HStack(spacing: 10) {
                    ForEach(row, id: \\.self) { button in
                        Button(action: { buttonTapped(button) }) {
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
    }
    
    func buttonWidth(_ button: String) -> CGFloat {
        button == "0" ? 170 : 80
    }
    
    func buttonColor(_ button: String) -> Color {
        if "0123456789.".contains(button) {
            return Color.gray
        } else if button == "=" {
            return Color.orange
        } else {
            return Color.blue
        }
    }
    
    func buttonTapped(_ button: String) {
        switch button {
        case "0"..."9":
            if display == "0" {
                display = button
            } else {
                display += button
            }
        case "C":
            display = "0"
            currentNumber = 0
            previousNumber = 0
            operation = ""
        case "+", "-", "×", "/":
            previousNumber = Double(display) ?? 0
            operation = button
            display = "0"
        case "=":
            currentNumber = Double(display) ?? 0
            switch operation {
            case "+": display = String(previousNumber + currentNumber)
            case "-": display = String(previousNumber - currentNumber)
            case "×": display = String(previousNumber * currentNumber)
            case "/": display = previousNumber != 0 ? String(previousNumber / currentNumber) : "Error"
            default: break
            }
        default:
            break
        }
    }
}"""
    
    def _weather_view(self) -> str:
        """Generate a weather app view"""
        return """import SwiftUI

struct ContentView: View {
    @State private var temperature = 72
    @State private var condition = "Partly Cloudy"
    @State private var cityName = "San Francisco"
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                Text(cityName)
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Image(systemName: "cloud.sun.fill")
                    .font(.system(size: 80))
                    .foregroundColor(.blue)
                
                Text("\\(temperature)°F")
                    .font(.system(size: 60))
                
                Text(condition)
                    .font(.title2)
                    .foregroundColor(.secondary)
                
                HStack(spacing: 30) {
                    VStack {
                        Image(systemName: "humidity")
                        Text("65%")
                        Text("Humidity")
                            .font(.caption)
                    }
                    
                    VStack {
                        Image(systemName: "wind")
                        Text("12 mph")
                        Text("Wind")
                            .font(.caption)
                    }
                }
                .padding()
                
                Spacer()
            }
            .padding()
            .navigationTitle("Weather")
        }
    }
}"""
    
    def _notes_view(self) -> str:
        """Generate a notes app view"""
        return """import SwiftUI

struct Note: Identifiable {
    let id = UUID()
    var title: String
    var content: String
    var date: Date = Date()
}

struct ContentView: View {
    @State private var notes: [Note] = []
    @State private var showingAddNote = false
    @State private var newNoteTitle = ""
    @State private var newNoteContent = ""
    
    var body: some View {
        NavigationView {
            List {
                ForEach(notes) { note in
                    VStack(alignment: .leading) {
                        Text(note.title)
                            .font(.headline)
                        Text(note.content)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .lineLimit(2)
                    }
                    .padding(.vertical, 4)
                }
                .onDelete(perform: deleteNotes)
            }
            .navigationTitle("Notes")
            .toolbar {
                Button(action: { showingAddNote = true }) {
                    Image(systemName: "plus")
                }
            }
            .sheet(isPresented: $showingAddNote) {
                NavigationView {
                    VStack {
                        TextField("Title", text: $newNoteTitle)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .padding()
                        
                        TextEditor(text: $newNoteContent)
                            .padding()
                        
                        Spacer()
                    }
                    .navigationTitle("New Note")
                    .toolbar {
                        ToolbarItem(placement: .navigationBarLeading) {
                            Button("Cancel") {
                                showingAddNote = false
                                newNoteTitle = ""
                                newNoteContent = ""
                            }
                        }
                        ToolbarItem(placement: .navigationBarTrailing) {
                            Button("Save") {
                                notes.append(Note(title: newNoteTitle, content: newNoteContent))
                                showingAddNote = false
                                newNoteTitle = ""
                                newNoteContent = ""
                            }
                        }
                    }
                }
            }
        }
    }
    
    func deleteNotes(at offsets: IndexSet) {
        notes.remove(atOffsets: offsets)
    }
}"""
    
    def _default_view(self, app_name: str, features: List[str]) -> str:
        """Generate a default view with requested features"""
        # Create a simple default app
        has_dark_mode = any('dark' in f.lower() for f in features)
        has_navigation = any('navigation' in f.lower() or 'nav' in f.lower() for f in features)
        
        view_code = """import SwiftUI

struct ContentView: View {"""
        
        if has_dark_mode:
            view_code += """
    @State private var isDarkMode = false"""
        
        view_code += f"""
    
    var body: some View {{"""
        
        if has_navigation:
            view_code += """
        NavigationView {"""
        
        view_code += f"""
            VStack(spacing: 20) {{
                Text("{app_name}")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Welcome to your new app!")
                    .font(.title2)
                    .foregroundColor(.secondary)"""
        
        if has_dark_mode:
            view_code += """
                
                Toggle("Dark Mode", isOn: $isDarkMode)
                    .padding()"""
        
        view_code += """
                
                Spacer()
            }
            .padding()"""
        
        if has_navigation:
            view_code += f"""
            .navigationTitle("{app_name}")"""
        
        if has_dark_mode:
            view_code += """
            .preferredColorScheme(isDarkMode ? .dark : .light)"""
        
        if has_navigation:
            view_code += """
        }"""
        
        view_code += """
    }
}"""
        
        return view_code

# Global instance
simple_generator = SimpleAppGenerator()