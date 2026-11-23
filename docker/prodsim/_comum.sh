# Funções comuns dos scripts da produção simulada. Use com: source _comum.sh
set -euo pipefail

PRODSIM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$PRODSIM_DIR")"

# shellcheck disable=SC1091
set -a; source "$PRODSIM_DIR/compose.env"; set +a

prodsim_compose() {
    docker compose \
        -f "$DOCKER_DIR/docker-compose-dev-mode-prod.yaml" \
        --env-file "$PRODSIM_DIR/compose.env" \
        "$@"
}

# Os scripts só falam com a simulação: qualquer alvo fora de localhost é recusado.
exige_localhost() {
    local url="$1"
    local host
    host="$(printf '%s' "$url" | sed -E 's#^[a-z]+://##; s#[/:].*$##')"
    case "$host" in
        localhost|127.0.0.1) ;;
        *) echo "Recusado: $url não é localhost. Estes scripts nunca acessam a produção." >&2; exit 2 ;;
    esac
}

container_rodando() {
    [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null || true)" = "true" ]
}

# Arquivos criados com sudo ficam com o dono de quem chamou o sudo.
devolve_ao_usuario() {
    if [ -n "${SUDO_USER:-}" ]; then
        chown -R "$SUDO_USER": "$@"
    fi
}
