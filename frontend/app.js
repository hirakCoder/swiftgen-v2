// SwiftGen AI - Modern Chat Interface with Complete Features
class SwiftGenChat {
    constructor() {
        this.ws = null;
        this.currentProjectId = null;
        this.generatedFiles = [];
        this.messageHistory = [];
        this.isProcessing = false;
        this.currentContext = {
            appName: '',
            description: '',
            features: []
        };
        this.projects = [];
        this.buildLogs = [];
        this.editingFile = null;
        
        // Track modification count for current session
        this.modificationCount = 0;
        
        // Track if generation is complete to prevent re-showing progress
        this.generationComplete = false;

        this.initializeEventListeners();
        this.setupTextareaAutoResize();
        this.initializeProgress();
        this.loadProjects();
        
        // Set initial status
        this.updateStatus('ready', 'Ready to create apps');
    }

    initializeEventListeners() {
        // Chat form submission
        document.getElementById('chatForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleChatSubmit();
        });

        // New project button
        document.getElementById('newChatBtn').addEventListener('click', () => {
            this.startNewProject();
        });
        
        // Don't connect WebSocket until we have a project
        // this.connectWebSocket('new');

        // Enter key handling for textarea
        document.getElementById('chatInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleChatSubmit();
            }
        });

        // View logs button
        document.addEventListener('click', (e) => {
            if (e.target.textContent === 'View Logs') {
                this.showBuildLogs();
            }
        });
    }
    // Add this method to open the code editor
    openCodeEditor() {
        if (!this.currentProjectId) {
            this.addMessage('assistant', 'Please create or load a project first to use the code editor.');
            return;
        }

        // Open editor in new tab/window
        const editorUrl = `/editor.html?project=${this.currentProjectId}`;
        window.open(editorUrl, '_blank');
    }

    setupTextareaAutoResize() {
        const textarea = document.getElementById('chatInput');
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        });
    }

    initializeProgress() {
        this.progressSteps = {
            generate: { percent: 20, text: 'Generating Swift code...', completed: false },
            create: { percent: 40, text: 'Creating project structure...', completed: false },
            build: { percent: 60, text: 'Building app...', completed: false },
            install: { percent: 80, text: 'Installing to simulator...', completed: false },
            launch: { percent: 100, text: 'Launching app...', completed: false }
        };

        // Reset progress state
        Object.keys(this.progressSteps).forEach(step => {
            this.progressSteps[step].completed = false;
        });
    }
    
    initializeModificationProgress() {
        // Use different progress steps for modifications
        this.progressSteps = {
            generate: { percent: 20, text: 'Analyzing modification...', completed: false },
            create: { percent: 40, text: 'Updating code...', completed: false },
            build: { percent: 60, text: 'Rebuilding app...', completed: false },
            install: { percent: 80, text: 'Reinstalling...', completed: false },
            launch: { percent: 100, text: 'Relaunching app...', completed: false }
        };

        // Reset progress state
        Object.keys(this.progressSteps).forEach(step => {
            this.progressSteps[step].completed = false;
        });
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            if (response.ok) {
                this.projects = await response.json();
                this.updateProjectsList();
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }

    updateProjectsList() {
        const projectInfo = document.getElementById('projectInfo');
        if (this.projects.length > 0) {
            projectInfo.innerHTML = `
                <select id="projectSelect" class="bg-dark-surface border border-dark-border rounded px-2 py-1 text-sm">
                    <option value="">Select a project</option>
                    ${this.projects.map(p => `
                        <option value="${p.project_id}">${p.app_name} - ${new Date(p.created_at).toLocaleDateString()}</option>
                    `).join('')}
                </select>
            `;

            document.getElementById('projectSelect').addEventListener('change', (e) => {
                if (e.target.value) {
                    this.loadProject(e.target.value);
                }
            });
        }
    }

    async loadProject(projectId) {
        try {
            const response = await fetch(`/api/project/${projectId}/status`);
            if (response.ok) {
                const project = await response.json();
                this.currentProjectId = projectId;
                this.currentContext = project.context || {};

                // Load project files
                const filesResponse = await fetch(`/api/project/${projectId}/files`);
                if (filesResponse.ok) {
                    const filesData = await filesResponse.json();
                    this.generatedFiles = filesData.files;
                    this.displayGeneratedCode(this.generatedFiles);
                }

                // Update UI
                document.getElementById('projectName').textContent = `Project: ${project.app_name}`;
                this.addMessage('assistant', `Loaded project: ${project.app_name}. You can now modify it or view the code.`);

                // Connect WebSocket
                this.connectWebSocket(projectId);
            }
        } catch (error) {
            console.error('Failed to load project:', error);
            this.addMessage('assistant', 'Failed to load project. Please try again.');
        }
    }

    async handleChatSubmit() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message) return;

        // Add user message to chat
        this.addMessage('user', message);

        // Clear input
        input.value = '';
        input.style.height = 'auto';

        // Debug logging
        console.log('Chat submit:', {
            hasWebSocket: !!this.ws,
            wsState: this.ws?.readyState,
            wsOpen: this.ws?.readyState === WebSocket.OPEN,
            currentProjectId: this.currentProjectId
        });
        
        // If WebSocket is connected, send through WebSocket for intelligent processing
        if (this.ws && this.ws.readyState === WebSocket.OPEN && this.currentProjectId) {
            console.log('Sending via WebSocket');
            this.ws.send(JSON.stringify({
                type: 'chat',
                content: message
            }));
        } else {
            console.log('Using local intent analysis');
            // Fallback to local intent analysis
            const intent = this.analyzeIntent(message);

            if (intent.type === 'create_app' && !this.currentProjectId) {
                // Only create new app if no project is active
                if (!this.isProcessing) {
                    await this.createNewApp(intent.appName, message);
                } else {
                    this.addMessage('assistant', "Please wait for the current operation to complete before creating a new app.");
                }
            } else if ((intent.type === 'modify_app' || intent.type === 'create_app') && this.currentProjectId) {
                // Modifications are now handled via WebSocket
                // The server will process and send real-time updates
                this.isProcessing = true;
            } else if (intent.type === 'question') {
                this.handleQuestion(message);
            } else {
                this.addMessage('assistant', "I can help you create or modify iOS apps. Try describing an app you'd like to build!");
            }
        }
    }

    analyzeIntent(message) {
        const lowerMessage = message.toLowerCase();

        // Check for app creation keywords
        const createKeywords = ['create', 'build', 'make', 'develop', 'new'];
        const hasCreateKeyword = createKeywords.some(keyword => lowerMessage.includes(keyword));

        // Check for modification keywords
        const modifyKeywords = ['add', 'change', 'modify', 'update', 'remove', 'delete', 'fix', 'edit'];
        const hasModifyKeyword = modifyKeywords.some(keyword => lowerMessage.includes(keyword));

        // Extract app name if mentioned
        let appName = 'MyApp';
        const appNameMatch = message.match(/(?:called?|named?)\s+["']?([^"']+)["']?/i);
        if (appNameMatch) {
            appName = appNameMatch[1].trim();
        }

        // If there's an active project, ANY request should be treated as modification
        if (this.currentProjectId) {
            return { type: 'modify_app' };
        }
        
        // If no active project, check if it's a create request
        if (hasCreateKeyword || !hasModifyKeyword) {
            return { type: 'create_app', appName };
        }
        
        // Default to question only if no project and has modify keywords
        return { type: 'question' };
    }

    async createNewApp(appName, description) {
        this.isProcessing = true;
        this.initializeProgress(); // Reset progress
        this.showProgress();
        this.buildLogs = []; // Clear previous logs

        // Update context
        this.currentContext = {
            appName,
            description,
            features: []
        };

        // Update project name display
        document.getElementById('projectName').textContent = `Building: ${appName}`;
        
        // Reset generation complete flag
        this.generationComplete = false;
        
        // Update status to show we're processing
        this.updateStatus('processing', 'Starting app generation...');

        // Show initial assistant response
        this.addMessage('assistant', `Great! I'll create ${appName} for you. Let me generate the Swift code and build it...`, true);

        try {
            // Generate project ID and connect WebSocket
            const projectId = `proj_${Math.random().toString(36).substr(2, 8)}`;
            this.currentProjectId = projectId;
            this.connectWebSocket(projectId);
            
            // Wait for WebSocket to connect
            await new Promise((resolve) => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    resolve();
                } else {
                    const checkConnection = setInterval(() => {
                        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                            clearInterval(checkConnection);
                            resolve();
                        }
                    }, 50);
                    // Timeout after 2 seconds
                    setTimeout(() => {
                        clearInterval(checkConnection);
                        resolve();
                    }, 2000);
                }
            });

            // Make API request with the project ID
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    app_name: appName,
                    description: description,
                    project_id: projectId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            // The new endpoint returns immediately with status "started"
            if (result.status === 'started') {
                // Generation will happen in background, updates via WebSocket
                console.log('Generation started, waiting for WebSocket updates...');
            } else if (result.status === 'success') {
                // Legacy handling for old endpoint format
                this.updateProgress('launch', 100);

                let successMessage = `✅ ${appName} has been successfully created and built!`;
                if (result.simulator_launched) {
                    successMessage += '\n\n📱 The app is now running in the iOS Simulator. Check your simulator to see it in action!';
                    this.showSimulatorStatus(true);
                }
                successMessage += '\n\nYou can now:\n• Ask me to make changes to the app\n• Edit the code directly\n• View build logs\n• Export your project';

                this.addMessage('assistant', successMessage);
                this.updateStatus('ready', 'App running in simulator');

                // Reload projects list
                this.loadProjects();
            } else if (result.status === 'failed') {
                this.addMessage('assistant', '❌ There was an error building the app. Let me check what went wrong...', false, result.errors);
                this.buildLogs = result.errors || [];
                this.hideProgress();
            }

        } catch (error) {
            console.error('Error:', error);
            this.addMessage('assistant', `❌ Failed to create app: ${error.message}`);
            this.hideProgress();
        } finally {
            this.isProcessing = false;
        }
    }


    async modifyExistingApp(request) {
        this.isProcessing = true;
        this.buildLogs = [];
        
        // Increment modification count
        this.modificationCount++;
        
        // CRITICAL: Reset generationComplete so progress shows for modifications
        this.generationComplete = false;
        
        // Initialize modification-specific progress
        this.initializeModificationProgress();
        this.showProgress();

        this.addMessage('assistant', `📝 Processing modification #${this.modificationCount}: "${request}"\n\nUpdating your app and relaunching...`, true);

        try {
            const response = await fetch('/api/modify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: this.currentProjectId,
                    modification: request,
                    context: this.currentContext
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            // Update context with modification history
            if (!this.currentContext.modifications) {
                this.currentContext.modifications = [];
            }
            this.currentContext.modifications.push({
                request: request,
                timestamp: new Date().toISOString(),
                success: result.status === 'success',
                number: this.modificationCount
            });

            // Update files display
            if (result.modified_files && result.modified_files.length > 0) {
                this.generatedFiles = result.modified_files;
                this.displayGeneratedCode(result.modified_files);
            }

            if (result.status === 'success') {
                this.updateProgress('launch', 100);

                let message = `✅ Modification #${this.modificationCount} completed!\n\n`;
                if (result.modification_summary) {
                    message += `What I did: ${result.modification_summary}\n\n`;
                }
                message += `📱 The app has been rebuilt and is now running in the simulator with your changes.\n\n`;
                message += `You can now:\n• See the changes in the simulator\n• Request another modification\n• View the updated code`;

                this.addMessage('assistant', message);
                this.updateStatus('ready', `App running (${this.modificationCount} modifications applied)`);
                
                // Hide progress after a short delay to show completion
                setTimeout(() => this.hideProgress(), 1000);
            } else if (result.status === 'failed') {
                this.hideProgress();
                const errors = result.errors || result.build_result?.errors || [];
                this.buildLogs = errors;
                
                let errorMessage = `❌ Modification #${this.modificationCount} failed.`;
                if (result.message) {
                    errorMessage += `\n\n${result.message}`;
                }
                
                this.addMessage('assistant', errorMessage, false, errors);
                this.updateStatus('error', 'Modification failed');
            } else {
                // Legacy handling
                this.addMessage('assistant', `❌ Modification #${this.modificationCount} failed. Check the errors below.`, false, result.build_result?.errors);
                this.buildLogs = result.build_result?.errors || [];
                this.hideProgress();
            }

        } catch (error) {
            console.error('Error:', error);
            this.addMessage('assistant', `❌ Failed to apply modification: ${error.message}`);
            this.hideProgress();
        } finally {
            this.isProcessing = false;
        }
    }

    handleQuestion(message) {
        // If there's an active project, treat any question as a potential modification
        if (this.currentProjectId) {
            // This shouldn't happen anymore due to analyzeIntent fix, but just in case
            this.modifyExistingApp(message);
            return;
        }
        
        // Handle general questions about SwiftGen when no project is active
        const responses = {
            'help': "I can help you create iOS apps using natural language! Just describe what you want to build, and I'll generate the Swift code and launch it in the simulator.",
            'features': "I can create various types of iOS apps including:\n• Todo lists\n• Calculators\n• Weather apps\n• Timers\n• Note-taking apps\n• Chat interfaces\n\nJust describe what you want!",
            'modify': "Once your app is created, you can ask me to modify it by describing the changes you want. For example: 'Add a delete button to the todo list' or 'Change the color scheme to dark mode'.",
            'export': "You can export your project by clicking the Export button in the code preview section. This will download all your Swift files as a zip."
        };

        const lowerMessage = message.toLowerCase();
        let response = responses.help;

        if (lowerMessage.includes('feature') || lowerMessage.includes('what can')) {
            response = responses.features;
        } else if (lowerMessage.includes('modify') || lowerMessage.includes('change')) {
            response = responses.modify;
        } else if (lowerMessage.includes('export') || lowerMessage.includes('download')) {
            response = responses.export;
        }

        this.addMessage('assistant', response);
    }

    addMessage(sender, content, isTyping = false, errors = null) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-enter';

        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="flex items-start space-x-3 justify-end">
                    <div class="flex-1 max-w-md">
                        <p class="text-sm font-medium text-gray-300 mb-1 text-right">You</p>
                        <div class="bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-lg p-4">
                            <p class="text-gray-200 whitespace-pre-wrap">${this.escapeHtml(content)}</p>
                        </div>
                        <p class="text-xs text-gray-500 mt-1 text-right">${timestamp}</p>
                    </div>
                    <div class="w-8 h-8 bg-gray-600 rounded-lg flex items-center justify-center flex-shrink-0">
                        <svg class="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                        </svg>
                    </div>
                </div>
            `;
        } else {
            let contentHtml = content.split('\n').map(line => `<p>${this.escapeHtml(line)}</p>`).join('');
            if (isTyping) {
                contentHtml = `<span class="typing-indicator">${contentHtml}</span>`;
            }

            if (errors && errors.length > 0) {
                contentHtml += `
                    <div class="mt-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                        <p class="text-sm font-medium text-red-400 mb-2">Build Errors:</p>
                        <ul class="text-sm text-red-300 space-y-1">
                            ${errors.map(error => `<li>• ${this.escapeHtml(error)}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            messageDiv.innerHTML = `
                <div class="flex items-start space-x-3">
                    <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    </div>
                    <div class="flex-1 max-w-md">
                        <p class="text-sm font-medium text-gray-300 mb-1">SwiftGen AI</p>
                        <div class="bg-dark-bg rounded-lg p-4">
                            <div class="text-gray-200 space-y-1">${contentHtml}</div>
                        </div>
                        <p class="text-xs text-gray-500 mt-1">${timestamp}</p>
                    </div>
                </div>
            `;
        }

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Store in history
        this.messageHistory.push({ sender, content, timestamp });
    }

    connectWebSocket(projectId) {
        if (this.ws) {
            this.ws.close();
        }

        const wsUrl = `ws://localhost:8000/ws/${projectId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            // Don't show connection status to user - they don't need to know
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateStatus('error', 'Connection error');
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateStatus('disconnected', 'Disconnected from server');
        };
    }

    handleWebSocketMessage(message) {
        console.log('WebSocket message:', message);
        
        // Ensure we have the necessary elements
        const progressText = document.getElementById('progressText');
        const progressContainer = document.getElementById('progressContainer');

        switch (message.type) {
            case 'connected':
                // Ignore connection messages - user doesn't need to see this
                break;
            case 'status':
                // CRITICAL: Reset generationComplete for any status update
                this.generationComplete = false;
                
                // Always show progress for status updates
                if (progressContainer && progressContainer.classList.contains('hidden')) {
                    progressContainer.classList.remove('hidden');
                }
                this.showProgress();
                
                // CRITICAL: Update progress text immediately for all status messages
                if (progressText && message.message) {
                    progressText.textContent = message.message;
                    console.log('Updated progress text to:', message.message);
                } else {
                    console.warn('Progress text element not found or no message:', {
                        progressTextElement: progressText,
                        message: message.message,
                        progressTextId: document.getElementById('progressText')
                    });
                }
                
                // Also handle through normal flow
                this.handleStatusUpdate(message.message);
                
                // Update status bar based on status type
                if (message.status === 'generating' || message.status === 'building' || 
                    message.status === 'modifying' || message.status === 'analyzing' ||
                    message.status === 'retrying' || message.status === 'validating' ||
                    message.status === 'healing' || message.status === 'initializing') {
                    this.updateStatus('processing', message.message);
                    this.isProcessing = true;
                } else if (message.status === 'error') {
                    this.updateStatus('error', message.message);
                    this.hideProgress();
                    this.isProcessing = false;
                }
                break;
            case 'complete':
                // Handle completion message
                this.hideProgress();
                this.isProcessing = false;
                
                if (message.status === 'failed') {
                    // Handle failed completion
                    if (message.errors && message.errors.length > 0) {
                        this.buildLogs = message.errors;
                        this.addMessage('assistant', 
                            message.message || '❌ Build failed. Please check the errors below and try again.', 
                            false, 
                            message.errors
                        );
                    } else {
                        this.addMessage('assistant', message.message || '❌ Generation failed');
                    }
                    this.updateStatus('error', 'Build failed');
                } else {
                    // Handle successful completion
                    if (message.message) {
                        this.addMessage('assistant', message.message);
                    }
                    if (message.app_name) {
                        this.updateStatus('ready', `${message.app_name} is running`);
                    }
                    
                    // Show simulator status if launched
                    if (message.simulator_launched) {
                        this.showSimulatorStatus(true);
                    }
                }
                
                // Re-enable input
                const input = document.getElementById('chatInput');
                const sendBtn = document.getElementById('sendButton') || document.querySelector('button[type="submit"]');
                if (input) input.disabled = false;
                if (sendBtn) sendBtn.disabled = false;
                break;
            case 'error':
                // Handle build/generation errors
                this.hideProgress();
                this.isProcessing = false;
                
                if (message.errors && message.errors.length > 0) {
                    this.buildLogs = message.errors;
                    this.addMessage('assistant', 
                        message.message || '❌ The build failed with errors. Let me check what went wrong...', 
                        false, 
                        message.errors
                    );
                } else {
                    this.addMessage('assistant', message.message || '❌ An error occurred during generation');
                }
                
                // Update status
                this.updateStatus('error', 'Build failed');
                
                // Re-enable input
                const errorInput = document.getElementById('chatInput');
                const errorSendBtn = document.getElementById('sendButton') || document.querySelector('button[type="submit"]');
                if (errorInput) errorInput.disabled = false;
                if (errorSendBtn) errorSendBtn.disabled = false;
                break;
            case 'chat_response':
                this.addMessage('assistant', message.message);
                break;
            case 'trigger_modification':
                // DEPRECATED - modifications now happen server-side
                console.log('Received deprecated trigger_modification message');
                break;
            case 'code_generated':
                if (message.files) {
                    this.generatedFiles = message.files;
                    this.displayGeneratedCode(message.files);
                }
                break;
            case 'modification_complete':
                // Handle modification completion
                this.hideProgress();
                this.isProcessing = false;
                if (message.message) {
                    this.addMessage('assistant', message.message);
                }
                if (message.files) {
                    this.generatedFiles = message.files;
                    this.displayGeneratedCode(message.files);
                }
                break;
        }
    }

    handleStatusUpdate(statusMessage) {
        console.log('Status update:', statusMessage);

        // Initialize modification progress if this is a modification
        if ((statusMessage.includes('modification') || statusMessage.includes('Modification') || 
             statusMessage.includes('Refining') || statusMessage.includes('retry')) && 
            (!this.progressSteps.generate || this.progressSteps.generate.text !== 'Analyzing modification...')) {
            this.initializeModificationProgress();
        }

        // Update progress based on status message - handle both creation and modification
        if (statusMessage.includes('Analyzing') || statusMessage.includes('analyzing')) {
            this.updateProgress('generate', 10);
        } else if (statusMessage.includes('modification request')) {
            // Modification-specific
            this.updateProgress('generate', 15);
        } else if (statusMessage.includes('Refining implementation')) {
            // Retry attempts
            this.updateProgress('generate', 25);
        } else if (statusMessage.includes('Updating') || statusMessage.includes('Modifying')) {
            // Modification-specific
            this.updateProgress('create', 40);
        } else if (statusMessage.includes('Creating unique') || statusMessage.includes('Architecting')) {
            this.updateProgress('generate', 15);
        } else if (statusMessage.includes('Generated') || statusMessage.includes('Swift files')) {
            this.updateProgress('generate', 20);
        } else if (statusMessage.includes('Validating')) {
            this.updateProgress('generate', 30);
        } else if (statusMessage.includes('Applying') && statusMessage.includes('fixes')) {
            this.updateProgress('generate', 35);
        } else if (statusMessage.includes('Building') && statusMessage.includes('project structure')) {
            this.updateProgress('create', 40);
        } else if (statusMessage.includes('Generating Xcode project')) {
            this.updateProgress('build', 50);
        } else if (statusMessage.includes('Building app') || statusMessage.includes('Rebuilding')) {
            this.updateProgress('build', 60);
        } else if (statusMessage.includes('Build completed')) {
            this.updateProgress('build', 70);
        } else if (statusMessage.includes('Preparing to launch')) {
            this.updateProgress('install', 80);
        } else if (statusMessage.includes('Installing') || statusMessage.includes('Reinstalling')) {
            this.updateProgress('install', 85);
        } else if (statusMessage.includes('Launching') || statusMessage.includes('Relaunching')) {
            this.updateProgress('launch', 95);
        } else if (statusMessage.includes('App launched successfully') || statusMessage.includes('App is already running')) {
            this.updateProgress('launch', 100);
        }

        // Update status text
        const progressText = document.getElementById('progressText');
        if (progressText) {
            progressText.textContent = statusMessage;
        }

        // Add to build logs
        this.buildLogs.push(`[${new Date().toLocaleTimeString()}] ${statusMessage}`);
    }

    showProgress() {
        // Don't show progress if generation is already complete
        if (this.generationComplete) return;
        
        const container = document.getElementById('statusPanel');
        if (container) {
            container.classList.remove('hidden');
            this.resetProgress();
            // Show initial progress immediately
            this.updateProgress('generate', 5);
            // Start timer
            this.startTimer();
        }
    }

    hideProgress() {
        const container = document.getElementById('statusPanel');
        if (container) {
            container.classList.add('hidden');
        }
        // Mark generation as complete
        this.generationComplete = true;
        // Stop timer
        this.stopTimer();
    }
    
    startTimer() {
        this.startTime = Date.now();
        this.timerInterval = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            const timerElement = document.getElementById('timerDisplay');
            if (timerElement) {
                timerElement.textContent = display;
            }
        }, 1000);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    resetProgress() {
        // Reset all progress stage indicators
        document.querySelectorAll('.progress-stage').forEach(stage => {
            stage.classList.remove('bg-blue-600', 'bg-green-600');
            stage.classList.add('bg-gray-800');
            // Reset icon colors
            const svg = stage.querySelector('svg');
            if (svg) {
                svg.classList.remove('text-white');
                svg.classList.add('text-gray-600');
            }
            
            // Reset stage label colors
            const stageContainer = stage.parentElement;
            const labelElement = stageContainer?.querySelector('p');
            if (labelElement) {
                labelElement.classList.remove('text-blue-400', 'text-green-400', 'font-medium');
                labelElement.classList.add('text-gray-500');
            }
        });

        // Reset progress tracking
        Object.keys(this.progressSteps).forEach(step => {
            this.progressSteps[step].completed = false;
        });
        
        // Reset timer
        const timerDisplay = document.getElementById('timerDisplay');
        if (timerDisplay) {
            timerDisplay.textContent = '0:00';
        }
    }

    updateProgress(step, overridePercent = null) {
        const stepConfig = this.progressSteps[step];
        if (!stepConfig) return;

        // Mark step as completed
        stepConfig.completed = true;

        // Map progress steps to stage IDs and labels
        const stepToStage = {
            'generate': { id: 'stage-design', label: 'Design' },
            'create': { id: 'stage-implement', label: 'Implement' },
            'build': { id: 'stage-build', label: 'Build' },
            'install': { id: 'stage-validate', label: 'Validate' },
            'launch': { id: 'stage-launch', label: 'Launch' }
        };

        // Update the corresponding stage
        const stageInfo = stepToStage[step];
        if (stageInfo) {
            const stage = document.getElementById(stageInfo.id);
            if (stage) {
                // Update stage appearance
                stage.classList.remove('bg-gray-800');
                stage.classList.add('bg-blue-600');
                
                // Update icon color
                const svg = stage.querySelector('svg');
                if (svg) {
                    svg.classList.remove('text-gray-600');
                    svg.classList.add('text-white');
                }
                
                // Update stage label to be more visible when active
                const stageContainer = stage.parentElement;
                const labelElement = stageContainer?.querySelector('p');
                if (labelElement) {
                    labelElement.classList.remove('text-gray-500');
                    labelElement.classList.add('text-blue-400', 'font-medium');
                }
                
                // Mark previous stages as complete
                const stages = ['stage-design', 'stage-implement', 'stage-build', 'stage-validate', 'stage-launch'];
                const currentIndex = stages.indexOf(stageInfo.id);
                for (let i = 0; i < currentIndex; i++) {
                    const prevStage = document.getElementById(stages[i]);
                    if (prevStage) {
                        prevStage.classList.remove('bg-gray-800', 'bg-blue-600');
                        prevStage.classList.add('bg-green-600');
                        const prevSvg = prevStage.querySelector('svg');
                        if (prevSvg) {
                            prevSvg.classList.remove('text-gray-600');
                            prevSvg.classList.add('text-white');
                        }
                        
                        // Update completed stage labels
                        const prevContainer = prevStage.parentElement;
                        const prevLabel = prevContainer?.querySelector('p');
                        if (prevLabel) {
                            prevLabel.classList.remove('text-gray-500');
                            prevLabel.classList.add('text-green-400');
                        }
                    }
                }
            }
        }

        // Progress is shown via stage indicators, no progress bar in this UI
    }

    displayGeneratedCode(files) {
        const codeDisplay = document.getElementById('codeDisplay');
        const noCodeMessage = document.getElementById('noCodeMessage');
        const fileTabs = document.getElementById('fileTabs');
        const fileTabsContainer = document.getElementById('fileTabsContainer');

        // Show code display, hide no-code message
        codeDisplay.classList.remove('hidden');
        noCodeMessage.classList.add('hidden');
        fileTabs.classList.remove('hidden');

        // Clear existing tabs
        fileTabsContainer.innerHTML = '';

        // Add action buttons with new Advanced Editor button
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'ml-auto flex items-center space-x-2';
        actionsDiv.innerHTML = `
        <button onclick="swiftgenChat.openCodeEditor()" class="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center space-x-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
            </svg>
            <span>Advanced Editor</span>
        </button>
        <button onclick="swiftgenChat.startEditMode()" class="px-3 py-1 text-xs bg-dark-surface hover:bg-dark-hover border border-dark-border rounded">
            <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            Quick Edit
        </button>
        <button onclick="swiftgenChat.exportProject()" class="px-3 py-1 text-xs bg-dark-surface hover:bg-dark-hover border border-dark-border rounded">
            <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            Export
        </button>
    `;

        // Create tab container
        const tabContainer = document.createElement('div');
        tabContainer.className = 'flex items-center space-x-2 flex-1';

        // Create tabs for each file
        files.forEach((file, index) => {
            const fileName = file.path.split('/').pop();
            const tab = document.createElement('button');
            tab.className = `px-4 py-2 text-sm font-medium transition-all ${
                index === 0
                    ? 'text-blue-400 border-b-2 border-blue-400'
                    : 'text-gray-400 hover:text-gray-200'
            }`;
            tab.textContent = fileName;
            tab.onclick = () => this.selectFile(index);
            tab.setAttribute('data-file-index', index);
            tabContainer.appendChild(tab);
        });

        fileTabsContainer.appendChild(tabContainer);
        fileTabsContainer.appendChild(actionsDiv);

        // Display first file
        if (files.length > 0) {
            this.selectFile(0);
        }
    }
    
    selectFile(index) {
        const files = this.generatedFiles;
        if (!files || index >= files.length) return;

        // Update tab selection
        document.querySelectorAll('[data-file-index]').forEach((tab, i) => {
            if (i === index) {
                tab.className = 'px-4 py-2 text-sm font-medium transition-all text-blue-400 border-b-2 border-blue-400';
            } else {
                tab.className = 'px-4 py-2 text-sm font-medium transition-all text-gray-400 hover:text-gray-200';
            }
        });

        // Display file content
        const file = files[index];
        const codeContent = document.getElementById('codeContent');
        if (codeContent) {
            // Escape HTML and preserve formatting
            const escapedContent = file.content
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
            
            codeContent.innerHTML = `<pre><code class="language-swift">${escapedContent}</code></pre>`;
            
            // Highlight syntax if Prism is available
            if (typeof Prism !== 'undefined') {
                Prism.highlightElement(codeContent.querySelector('code'));
            }
        }
    }
    
    async saveFileChanges() {
        const codeContent = document.getElementById('codeContent');
        const editButton = document.querySelector('button[onclick="swiftgenChat.startEditMode()"]');

        // Get the edited content
        const newContent = codeContent.textContent;
        const file = this.generatedFiles[this.editingFile];

        // Update local file content
        file.content = newContent;

        // Exit edit mode
        codeContent.contentEditable = false;
        codeContent.className = 'text-sm text-gray-300';
        this.editingFile = null;

        editButton.innerHTML = `
            <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            Edit
        `;
        editButton.className = 'px-3 py-1 text-xs bg-dark-surface hover:bg-dark-hover border border-dark-border rounded';

        // Send update to backend
        try {
            const response = await fetch('/api/modify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: this.currentProjectId,
                    modification: 'Manual code edit',
                    context: {
                        ...this.currentContext,
                        manual_edit: true,
                        edited_files: [file]
                    }
                })
            });

            if (response.ok) {
                this.addMessage('assistant', '✅ Changes saved and app rebuilt successfully!');
            } else {
                this.addMessage('assistant', '❌ Failed to save changes. Please try again.');
            }
        } catch (error) {
            console.error('Save error:', error);
            this.addMessage('assistant', '❌ Error saving changes: ' + error.message);
        }
    }

    async exportProject() {
        if (!this.currentProjectId || this.generatedFiles.length === 0) {
            this.addMessage('assistant', 'No project to export. Please create an app first.');
            return;
        }

        // Create a zip file content
        const zip = new JSZip();

        // Add all files to zip
        this.generatedFiles.forEach(file => {
            zip.file(file.path, file.content);
        });

        // Add project info
        const projectInfo = {
            app_name: this.currentContext.appName,
            description: this.currentContext.description,
            created_at: new Date().toISOString(),
            exported_at: new Date().toISOString()
        };
        zip.file('project_info.json', JSON.stringify(projectInfo, null, 2));

        // Generate and download zip
        try {
            const content = await zip.generateAsync({ type: 'blob' });
            const url = URL.createObjectURL(content);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${this.currentContext.appName || 'SwiftGenApp'}.zip`;
            a.click();
            URL.revokeObjectURL(url);

            this.addMessage('assistant', `✅ Project exported successfully as ${a.download}`);
        } catch (error) {
            console.error('Export error:', error);
            this.addMessage('assistant', '❌ Failed to export project. Please try again.');
        }
    }

    showBuildLogs() {
        if (this.buildLogs.length === 0) {
            this.addMessage('assistant', 'No build logs available yet. Create or modify an app to see logs.');
            return;
        }

        // Create a modal or expanded view for logs
        const logsHtml = this.buildLogs.map(log => `<div class="text-xs text-gray-400 font-mono">${this.escapeHtml(log)}</div>`).join('');

        this.addMessage('assistant', `<div class="mt-2 p-3 bg-dark-surface rounded-lg border border-dark-border">
            <p class="text-sm font-medium text-gray-300 mb-2">Build Logs:</p>
            <div class="space-y-1 max-h-60 overflow-y-auto">
                ${logsHtml}
            </div>
        </div>`);
    }

    showSimulatorStatus(isRunning) {
        const statusDiv = document.getElementById('simulatorStatus');
        if (isRunning) {
            statusDiv.classList.remove('hidden');
        } else {
            statusDiv.classList.add('hidden');
        }
    }

    updateStatus(type, message) {
        const indicator = document.getElementById('statusIndicator');
        const text = document.getElementById('statusText');

        if (!indicator || !text) return;

        const statusConfig = {
            'ready': { color: 'bg-green-500', text: message || 'Ready to create apps' },
            'connected': { color: 'bg-green-500', text: 'Ready' }, // Don't show technical details
            'processing': { color: 'bg-yellow-500', text: message || 'Processing...' },
            'error': { color: 'bg-red-500', text: message || 'Error occurred' },
            'disconnected': { color: 'bg-gray-500', text: 'Reconnecting...' }
        };

        const config = statusConfig[type] || statusConfig.ready;
        indicator.className = `w-2 h-2 rounded-full ${config.color}`;
        text.textContent = config.text;
    }

    startNewProject() {
        if (this.isProcessing) {
            alert('Please wait for the current process to complete.');
            return;
        }

        // Reset state
        this.currentProjectId = null;
        this.generatedFiles = [];
        this.currentContext = { appName: '', description: '', features: [] };
        this.buildLogs = [];
        this.editingFile = null;

        // Clear UI
        document.getElementById('chatMessages').innerHTML = '';
        document.getElementById('codeContent').textContent = '';
        document.getElementById('fileTabsContainer').innerHTML = '';
        document.getElementById('codeDisplay').classList.add('hidden');
        document.getElementById('noCodeMessage').classList.remove('hidden');
        document.getElementById('fileTabs').classList.add('hidden');
        document.getElementById('simulatorStatus').classList.add('hidden');
        document.getElementById('projectName').textContent = 'Start by describing your app idea';

        // Show welcome message again
        this.addMessage('assistant', "👋 Ready to create a new iOS app! What would you like to build?");

        // Focus on input
        document.getElementById('chatInput').focus();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Add JSZip library for export functionality
const script = document.createElement('script');
script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
document.head.appendChild(script);

// Initialize the chat interface
// DISABLED: Using SwiftGenApp from index.html instead
// document.addEventListener('DOMContentLoaded', () => {
//     window.swiftgenChat = new SwiftGenChat();
// });
