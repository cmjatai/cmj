
// JavaScript para o dashboard de cronômetros

class TimerDashboard {
    constructor() {
        this.timers = new Map();
        this.websockets = new Map();
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadAllTimers();
        this.updateStatistics();
        this.startPeriodicUpdates();
    }

    bindEvents() {
        // Eventos dos botões de controle
        document.addEventListener('click', (e) => {
            if (e.target.matches('.timer-start') || e.target.closest('.timer-start')) {
                const btn = e.target.matches('.timer-start') ? e.target : e.target.closest('.timer-start');
                this.startTimer(btn.dataset.timerId);
            } else if (e.target.matches('.timer-pause') || e.target.closest('.timer-pause')) {
                const btn = e.target.matches('.timer-pause') ? e.target : e.target.closest('.timer-pause');
                this.pauseTimer(btn.dataset.timerId);
            } else if (e.target.matches('.timer-resume') || e.target.closest('.timer-resume')) {
                const btn = e.target.matches('.timer-resume') ? e.target : e.target.closest('.timer-resume');
                this.resumeTimer(btn.dataset.timerId);
            } else if (e.target.matches('.timer-stop') || e.target.closest('.timer-stop')) {
                const btn = e.target.matches('.timer-stop') ? e.target : e.target.closest('.timer-stop');
                this.stopTimer(btn.dataset.timerId);
            }
        });

        // Formulário de criar cronômetro
        const createForm = document.getElementById('createTimerForm');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createTimer();
            });
        }
    }

    async loadAllTimers() {
        try {
            const response = await fetch('/api/timers/');
            const timers = await response.json();
            
            timers.results.forEach(timer => {
                this.timers.set(timer.id, timer);
                this.connectWebSocket(timer.id);
            });
        } catch (error) {
            console.error('Erro ao carregar cronômetros:', error);
            this.showToast('Erro ao carregar cronômetros', 'error');
        }
    }

    connectWebSocket(timerId) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/timer/${timerId}/`;
        
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log(`WebSocket conectado para timer ${timerId}`);
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        ws.onclose = () => {
            console.log(`WebSocket desconectado para timer ${timerId}`);
            // Tentar reconectar após 3 segundos
            setTimeout(() => this.connectWebSocket(timerId), 3000);
        };
        
        ws.onerror = (error) => {
            console.error(`Erro WebSocket para timer ${timerId}:`, error);
        };
        
        this.websockets.set(timerId, ws);
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'timer_update':
                this.updateTimerRow(data);
                break;
            case 'child_update':
                this.handleChildUpdate(data);
                break;
            case 'command_result':
                this.handleCommandResult(data);
                break;
            case 'error':
                this.showToast(data.message, 'error');
                break;
        }
    }

    updateTimerRow(data) {
        const row = document.getElementById(`timer-row-${data.timer_id}`);
        if (!row) return;

        // Atualizar estado
        const stateBadge = row.querySelector('.state-badge');
        if (stateBadge) {
            stateBadge.className = `badge state-badge state-${data.state}`;
            stateBadge.textContent = this.getStateDisplayName(data.state);
        }

        // Atualizar tempo decorrido
        const elapsedCell = row.querySelector('.elapsed-time');
        if (elapsedCell) {
            elapsedCell.textContent = this.formatTime(data.elapsed_time);
        }

        // Atualizar tempo restante
        const remainingCell = row.querySelector('.remaining-time');
        if (remainingCell) {
            remainingCell.textContent = this.formatTime(data.remaining_time);
        }

        // Atualizar botões
        this.updateTimerButtons(data.timer_id, data.state);

        // Highlight da mudança
        row.classList.add('highlight-change');
        setTimeout(() => row.classList.remove('highlight-change'), 1000);

        // Atualizar estatísticas
        this.updateStatistics();
    }

    updateTimerButtons(timerId, state) {
        const row = document.getElementById(`timer-row-${timerId}`);
        if (!row) return;

        const startBtn = row.querySelector('.timer-start');
        const pauseBtn = row.querySelector('.timer-pause');
        const resumeBtn = row.querySelector('.timer-resume');
        const stopBtn = row.querySelector('.timer-stop');

        // Resetar todos os botões
        [startBtn, pauseBtn, resumeBtn, stopBtn].forEach(btn => {
            if (btn) btn.disabled = true;
        });

        // Habilitar botões baseado no estado
        switch (state) {
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
            case 'finished':
                // Nenhum botão habilitado para cronômetros finalizados
                break;
        }
    }

    async startTimer(timerId) {
        await this.sendCommand(timerId, 'start');
    }

    async pauseTimer(timerId) {
        await this.sendCommand(timerId, 'pause');
    }

    async resumeTimer(timerId) {
        await this.sendCommand(timerId, 'resume');
    }

    async stopTimer(timerId) {
        await this.sendCommand(timerId, 'stop');
    }

    async sendCommand(timerId, command) {
        try {
            const response = await fetch(`/api/timers/${timerId}/${command}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();
            
            if (result.success) {
                this.showToast(`Cronômetro ${command === 'start' ? 'iniciado' : 
                                command === 'pause' ? 'pausado' : 
                                command === 'resume' ? 'retomado' : 'parado'} com sucesso!`, 'success');
            } else {
                this.showToast(result.error || 'Erro na operação', 'error');
            }
        } catch (error) {
            console.error(`Erro ao executar ${command}:`, error);
            this.showToast('Erro na operação', 'error');
        }
    }

    async createTimer() {
        const form = document.getElementById('createTimerForm');
        const formData = new FormData(form);
        
        // Converter tempo para duration format
        const hours = parseInt(formData.get('hours') || 0);
        const minutes = parseInt(formData.get('minutes') || 0);
        const seconds = parseInt(formData.get('seconds') || 0);
        const duration = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        const timerData = {
            name: formData.get('name'),
            duration: duration,
            parent: formData.get('parent') || null,
            stop_parent_on_finish: formData.has('stop_parent_on_finish'),
            reduce_parent_time: formData.has('reduce_parent_time')
        };

        try {
            const response = await fetch('/api/timers/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(timerData)
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showToast('Cronômetro criado com sucesso!', 'success');
                // Fechar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('createTimerModal'));
                modal.hide();
                // Recarregar página
                window.location.reload();
            } else {
                this.showToast('Erro ao criar cronômetro', 'error');
            }
        } catch (error) {
            console.error('Erro ao criar cronômetro:', error);
            this.showToast('Erro ao criar cronômetro', 'error');
        }
    }

    updateStatistics() {
        const states = {
            running: 0,
            paused: 0,
            stopped: 0,
            finished: 0
        };

        document.querySelectorAll('[data-timer-id]').forEach(row => {
            const stateBadge = row.querySelector('.state-badge');
            if (stateBadge) {
                const state = stateBadge.className.match(/state-(\w+)/);
                if (state && states.hasOwnProperty(state[1])) {
                    states[state[1]]++;
                }
            }
        });

        // Atualizar elementos na página
        const runningEl = document.getElementById('runningTimers');
        const pausedEl = document.getElementById('pausedTimers');
        const stoppedEl = document.getElementById('stoppedTimers');
        
        if (runningEl) runningEl.textContent = states.running;
        if (pausedEl) pausedEl.textContent = states.paused;
        if (stoppedEl) stoppedEl.textContent = states.stopped;
    }

    startPeriodicUpdates() {
        // Atualizar estatísticas a cada 5 segundos
        setInterval(() => {
            this.updateStatistics();
        }, 5000);
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
        // Criar toast container se não existir
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
        
        // Remover do DOM após esconder
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.timerDashboard = new TimerDashboard();
});

// Função global para refresh
function refreshAllTimers() {
    if (window.timerDashboard) {
        window.location.reload();
    }
}
