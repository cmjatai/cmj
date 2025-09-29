
// JavaScript comum para funcionalidades gerais de cronômetros

// Utilitários globais
window.TimerUtils = {
    formatTime: function(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },

    parseTime: function(timeString) {
        const parts = timeString.split(':');
        return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
    },

    getStateDisplayName: function(state) {
        const names = {
            'stopped': 'Parado',
            'running': 'Executando',
            'paused': 'Pausado',
            'finished': 'Finalizado'
        };
        return names[state] || state;
    },

    getCSRFToken: function() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    },

    showNotification: function(message, type = 'info', duration = 5000) {
        // Criar notificação no estilo toast
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        notification.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-hide
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
        
        return notification;
    },

    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    },

    validateDuration: function(hours, minutes, seconds) {
        hours = parseInt(hours) || 0;
        minutes = parseInt(minutes) || 0;  
        seconds = parseInt(seconds) || 0;
        
        if (hours < 0 || hours > 23) return false;
        if (minutes < 0 || minutes > 59) return false;
        if (seconds < 0 || seconds > 59) return false;
        if (hours === 0 && minutes === 0 && seconds === 0) return false;
        
        return true;
    },

    formatDuration: function(hours, minutes, seconds) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
};

// Event listeners globais
document.addEventListener('DOMContentLoaded', function() {
    // Melhorar acessibilidade - adicionar tooltips
    const tooltips = document.querySelectorAll('[title]');
    tooltips.forEach(element => {
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            new bootstrap.Tooltip(element);
        }
    });

    // Confirmar ações perigosas
    document.addEventListener('click', function(e) {
        if (e.target.matches('.timer-stop') || e.target.closest('.timer-stop')) {
            if (!confirm('Tem certeza que deseja parar este cronômetro?')) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        }
    });

    // Validação do formulário de criar cronômetro
    const createForm = document.getElementById('createTimerForm');
    if (createForm) {
        createForm.addEventListener('submit', function(e) {
            const hours = parseInt(document.getElementById('hours')?.value) || 0;
            const minutes = parseInt(document.getElementById('minutes')?.value) || 0;
            const seconds = parseInt(document.getElementById('seconds')?.value) || 0;
            
            if (!TimerUtils.validateDuration(hours, minutes, seconds)) {
                e.preventDefault();
                TimerUtils.showNotification('Por favor, insira uma duração válida (maior que 00:00:00)', 'error');
                return false;
            }
            
            const name = document.getElementById('timerName')?.value?.trim();
            if (!name || name.length < 3) {
                e.preventDefault();
                TimerUtils.showNotification('Nome do cronômetro deve ter pelo menos 3 caracteres', 'error');
                return false;
            }
        });
    }

    // Auto-save para configurações (com debounce)
    const configSwitches = document.querySelectorAll('.form-check-input[data-timer-id]');
    const debouncedSave = TimerUtils.debounce(function(timerId, field, value) {
        // Esta função será implementada em cada página específica
        if (window.timerDetail && typeof window.timerDetail.updateTimerConfig === 'function') {
            window.timerDetail.updateTimerConfig(field, value);
        }
    }, 1000);
    
    configSwitches.forEach(switchEl => {
        switchEl.addEventListener('change', function() {
            const timerId = this.dataset.timerId;
            const field = this.id === 'stopParentSwitch' ? 'stop_parent_on_finish' : 'reduce_parent_time';
            debouncedSave(timerId, field, this.checked);
        });
    });
});

// Função para carregar cronômetros disponíveis no select de cronômetro pai
function loadParentTimerOptions() {
    fetch('/api/timers/')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('parentTimer');
            if (!select) return;
            
            // Limpar opções existentes (exceto a primeira)
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            // Adicionar cronômetros como opções
            data.results.forEach(timer => {
                const option = document.createElement('option');
                option.value = timer.id;
                option.textContent = `${timer.name} (${TimerUtils.getStateDisplayName(timer.state)})`;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Erro ao carregar cronômetros:', error);
        });
}

// Carregar opções quando modal é aberto
document.addEventListener('shown.bs.modal', function(e) {
    if (e.target.id === 'createTimerModal') {
        loadParentTimerOptions();
    }
});

// Função para refresh geral
window.refreshPage = function() {
    window.location.reload();
};

// Registrar service worker para notificações (se suportado)
if ('serviceWorker' in navigator && 'Notification' in window) {
    // Registrar service worker para funcionalidades futuras
    navigator.serviceWorker.register('/sw.js').catch(error => {
        console.log('Service Worker registration failed:', error);
    });
    
    // Solicitar permissão para notificações
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Função para enviar notificação de timer finalizado
window.showTimerFinishedNotification = function(timerName) {
    if (Notification.permission === 'granted') {
        const notification = new Notification('Cronômetro Finalizado!', {
            body: `O cronômetro "${timerName}" foi finalizado.`,
            icon: '/static/timer_app/img/timer-icon.png',
            tag: 'timer-finished',
            requireInteraction: true
        });
        
        notification.onclick = function() {
            window.focus();
            notification.close();
        };
        
        // Auto-close após 10 segundos
        setTimeout(() => notification.close(), 10000);
    }
};
