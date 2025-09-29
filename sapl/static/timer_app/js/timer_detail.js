
// JavaScript para página de detalhes do cronômetro

class TimerDetail {
    constructor(timerId, duration, treeData) {
        this.timerId = timerId;
        this.duration = duration;
        this.treeData = treeData;
        this.websocket = null;
        this.updateInterval = null;
        this.currentState = 'stopped';
        this.startTime = null;
        this.elapsedSeconds = 0;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.connectWebSocket();
        this.renderTree();
        this.startLocalTimer();
    }

    bindEvents() {
        // Botões de controle
        document.addEventListener('click', (e) => {
            if (e.target.matches('.timer-start') || e.target.closest('.timer-start')) {
                this.startTimer();
            } else if (e.target.matches('.timer-pause') || e.target.closest('.timer-pause')) {
                this.pauseTimer();
            } else if (e.target.matches('.timer-resume') || e.target.closest('.timer-resume')) {
                this.resumeTimer();
            } else if (e.target.matches('.timer-stop') || e.target.closest('.timer-stop')) {
                this.stopTimer();
            }
        });

        // Switches de configuração
        const stopParentSwitch = document.getElementById('stopParentSwitch');
        const reduceParentSwitch = document.getElementById('reduceParentSwitch');

        if (stopParentSwitch) {
            stopParentSwitch.addEventListener('change', () => {
                this.updateTimerConfig('stop_parent_on_finish', stopParentSwitch.checked);
            });
        }

        if (reduceParentSwitch) {
            reduceParentSwitch.addEventListener('change', () => {
                this.updateTimerConfig('reduce_parent_time', reduceParentSwitch.checked);
            });
        }
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/timer/${this.timerId}/`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            this.updateConnectionStatus('connected');
            console.log('WebSocket conectado');
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.websocket.onclose = () => {
            this.updateConnectionStatus('disconnected');
            console.log('WebSocket desconectado');
            // Tentar reconectar
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.websocket.onerror = (error) => {
            this.updateConnectionStatus('disconnected');
            console.error('Erro WebSocket:', error);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'timer_state':
                this.updateTimerState(data.timer);
                break;
            case 'timer_update':
                this.updateTimerDisplay(data);
                break;
            case 'child_update':
                this.updateChildDisplay(data);
                break;
            case 'command_result':
                this.handleCommandResult(data);
                break;
            case 'error':
                this.showToast(data.message, 'error');
                break;
        }
    }

    updateTimerState(timerData) {
        this.currentState = timerData.state;
        this.elapsedSeconds = timerData.elapsed_time;
        
        this.updateDisplay();
        this.updateButtons();
    }

    updateTimerDisplay(data) {
        this.currentState = data.state;
        this.elapsedSeconds = data.elapsed_time;
        
        this.updateDisplay();
        this.updateButtons();
    }

    updateChildDisplay(data) {
        const childElement = document.querySelector(`[data-child-id="${data.child_timer_id}"]`);
        if (childElement) {
            const stateElement = childElement.querySelector(`.child-state-${data.child_timer_id}`);
            if (stateElement) {
                stateElement.textContent = this.getStateDisplayName(data.state);
                stateElement.className = `text-muted child-state-${data.child_timer_id} state-${data.state}`;
            }
        }
    }

    updateDisplay() {
        // Atualizar tempo decorrido
        const elapsedEl = document.getElementById('elapsedTime');
        if (elapsedEl) {
            elapsedEl.textContent = this.formatTime(this.elapsedSeconds);
        }

        // Atualizar tempo restante
        const remainingSeconds = Math.max(0, this.duration - this.elapsedSeconds);
        const remainingEl = document.getElementById('remainingTime');
        if (remainingEl) {
            remainingEl.textContent = this.formatTime(remainingSeconds);
        }

        // Atualizar barra de progresso
        this.updateProgressBar();

        // Atualizar badge de estado
        const stateBadges = document.querySelectorAll('.state-badge');
        stateBadges.forEach(badge => {
            badge.className = `badge state-badge state-${this.currentState} fs-6`;
            badge.textContent = this.getStateDisplayName(this.currentState);
        });
    }

    updateProgressBar() {
        const progress = (this.elapsedSeconds / this.duration) * 100;
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (progressBar) {
            progressBar.style.width = `${Math.min(progress, 100)}%`;
            progressBar.setAttribute('aria-valuenow', Math.min(progress, 100));
        }
        
        if (progressText) {
            progressText.textContent = `${Math.round(Math.min(progress, 100))}%`;
        }
        
        // Mudar cor da barra baseado no progresso
        if (progressBar) {
            if (progress < 50) {
                progressBar.style.background = 'linear-gradient(90deg, #4facfe 0%, #00f2fe 100%)';
            } else if (progress < 80) {
                progressBar.style.background = 'linear-gradient(90deg, #ffc107 0%, #ff8c00 100%)';
            } else {
                progressBar.style.background = 'linear-gradient(90deg, #dc3545 0%, #ff6b6b 100%)';
            }
        }
    }

    updateButtons() {
        const startBtn = document.querySelector('.timer-start');
        const pauseBtn = document.querySelector('.timer-pause');
        const resumeBtn = document.querySelector('.timer-resume');
        const stopBtn = document.querySelector('.timer-stop');

        // Resetar todos os botões
        [startBtn, pauseBtn, resumeBtn, stopBtn].forEach(btn => {
            if (btn) btn.disabled = true;
        });

        // Habilitar botões baseado no estado
        switch (this.currentState) {
            case 'stopped':
                if (startBtn) startBtn.disabled = false;
                break;
            case 'running':
                if (pauseBtn) pauseBtn.disabled = false;
                if (stopBtn) stopBtn.disabled = false;
                break;
            case 'paused':
                if (resumeBtn) resumeBtn.disabled = false;
                if (stopBtn) stopBtn.disabled = false;
                break;
        }
    }

    startLocalTimer() {
        this.updateInterval = setInterval(() => {
            if (this.currentState === 'running') {
                this.elapsedSeconds++;
                this.updateDisplay();
                
                // Verificar se terminou
                if (this.elapsedSeconds >= this.duration) {
                    this.currentState = 'finished';
                    this.updateDisplay();
                    this.updateButtons();
                    clearInterval(this.updateInterval);
                }
            }
        }, 1000);
    }

    renderTree() {
        const treeContainer = document.getElementById('timerTree');
        if (!treeContainer || !this.treeData) return;

        const renderNode = (node, level = 0) => {
            const indent = '  '.repeat(level);
            const icon = node.state === 'running' ? '▶' : 
                        node.state === 'paused' ? '⏸' :
                        node.state === 'finished' ? '✓' : '⏹';
            
            return `
                <div class="timer-tree-node ${node.state}" style="margin-left: ${level * 20}px;">
                    ${icon} ${node.name} (${this.getStateDisplayName(node.state)})
                    ${node.children ? node.children.map(child => renderNode(child, level + 1)).join('') : ''}
                </div>
            `;
        };

        treeContainer.innerHTML = renderNode(this.treeData);
    }

    async startTimer() {
        await this.sendCommand('start');
    }

    async pauseTimer() {
        await this.sendCommand('pause');
    }

    async resumeTimer() {
        await this.sendCommand('resume');
    }

    async stopTimer() {
        await this.sendCommand('stop');
    }

    async sendCommand(command) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                command: command,
                timer_id: this.timerId
            }));
        } else {
            // Fallback para HTTP se WebSocket não disponível
            try {
                const response = await fetch(`/api/timers/${this.timerId}/${command}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'Content-Type': 'application/json',
                    }
                });

                const result = await response.json();
                this.handleCommandResult({ command, result });
            } catch (error) {
                console.error(`Erro ao executar ${command}:`, error);
                this.showToast('Erro na operação', 'error');
            }
        }
    }

    async updateTimerConfig(field, value) {
        try {
            const response = await fetch(`/api/timers/${this.timerId}/`, {
                method: 'PATCH',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    [field]: value
                })
            });

            if (response.ok) {
                this.showToast('Configuração atualizada!', 'success');
            } else {
                this.showToast('Erro ao atualizar configuração', 'error');
            }
        } catch (error) {
            console.error('Erro ao atualizar configuração:', error);
            this.showToast('Erro ao atualizar configuração', 'error');
        }
    }

    handleCommandResult(data) {
        if (data.result && data.result.success) {
            const actionNames = {
                'start': 'iniciado',
                'pause': 'pausado',
                'resume': 'retomado',
                'stop': 'parado'
            };
            this.showToast(`Cronômetro ${actionNames[data.command]}!`, 'success');
        } else {
            this.showToast(data.result?.error || 'Erro na operação', 'error');
        }
    }

    updateConnectionStatus(status) {
        const statusEl = document.getElementById('wsStatus');
        if (statusEl) {
            statusEl.className = `badge bg-${status === 'connected' ? 'success' : 'danger'}`;
            statusEl.innerHTML = `<i class="fas fa-circle me-1"></i>${status === 'connected' ? 'Conectado' : 'Desconectado'}`;
        }
    }

    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    getStateDisplayName(state) {
        const names = {
            'stopped': 'Parado',
            'running': 'Executando',
            'paused': 'Pausado',
            'finished': 'Finalizado'
        };
        return names[state] || state;
    }

    showToast(message, type = 'info') {
        // Mesmo código do dashboard.js
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast custom-toast`;
        toast.innerHTML = `
            <div class="toast-header bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'} text-white">
                <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
                <strong class="me-auto">${type === 'error' ? 'Erro' : type === 'success' ? 'Sucesso' : 'Info'}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;

        container.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 5000
        });
        
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // Variáveis são definidas no template HTML
    if (typeof TIMER_ID !== 'undefined' && typeof TIMER_DURATION !== 'undefined') {
        const treeData = typeof TREE_DATA !== 'undefined' ? TREE_DATA : null;
        window.timerDetail = new TimerDetail(TIMER_ID, TIMER_DURATION, treeData);
    }
});
