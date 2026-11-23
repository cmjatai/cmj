#!/usr/bin/env bash
# Sobe a produção simulada. Uso: sudo docker/prodsim/up.sh [--green] [--no-build]
source "$(dirname "$0")/_comum.sh"

PERFIS=()
BUILD=(--build)
for arg in "$@"; do
    case "$arg" in
        --green) PERFIS=(--profile green) ;;
        --no-build) BUILD=() ;;
        *) echo "Opção desconhecida: $arg" >&2; exit 2 ;;
    esac
done

[ -f "$PRODSIM_DIR/certs/prodsim.crt" ] || bash "$PRODSIM_DIR/gen-cert.sh"

if [ ! -f "$PRODSIM_DIR/cmj.env" ]; then
    SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
    sed "s#__GERADO_PELO_UP_SH__#${SECRET}#" "$PRODSIM_DIR/cmj.env.example" > "$PRODSIM_DIR/cmj.env"
    chmod 644 "$PRODSIM_DIR/cmj.env"
    devolve_ao_usuario "$PRODSIM_DIR/cmj.env"
    echo "Criado $PRODSIM_DIR/cmj.env a partir do exemplo."
fi

# Versão da imagem (docs/specs/infra/versionamento.md). O git roda como quem chamou o sudo: como
# root ele recusa o repositório de outro dono.
RAIZ="$(dirname "$DOCKER_DIR")"
if [ -n "${SUDO_USER:-}" ]; then
    PORTALCMJ_VERSION="$(sudo -u "$SUDO_USER" python3 "$RAIZ/cmj/core/services/s_versao.py")"
else
    PORTALCMJ_VERSION="$(python3 "$RAIZ/cmj/core/services/s_versao.py")"
fi
export PORTALCMJ_VERSION
echo "Versão: $PORTALCMJ_VERSION"

prodsim_compose "${PERFIS[@]}" up -d "${BUILD[@]}"

echo
echo "Produção simulada no ar (o container da aplicação roda migrate e cria as coleções do Solr ao subir):"
echo "  portal      https://localhost:${PRODSIM_HTTPS_PORT}  (certificado autoassinado)"
echo "  grafana     http://127.0.0.1:${GRAFANA_PORT}  (admin / ${GRAFANA_ADMIN_PASSWORD})"
echo "  prometheus  http://127.0.0.1:${PROMETHEUS_PORT}"
echo "  logs        sudo docker logs -f prodsim-cmj-blue"
echo
echo "Banco vazio? Copie o do dev com: sudo docker/prodsim/db-from-dev.sh"
echo "Depois de subir: sudo docker/prodsim/smoke.sh"
