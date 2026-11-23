#!/usr/bin/env bash
# Gera o certificado autoassinado do nginx da frente (certs/ é ignorado pelo git).
source "$(dirname "$0")/_comum.sh"

mkdir -p "$PRODSIM_DIR/certs"
if [ -f "$PRODSIM_DIR/certs/prodsim.crt" ] && [ "${1:-}" != "--force" ]; then
    echo "Certificado já existe em $PRODSIM_DIR/certs (use --force para gerar outro)."
    exit 0
fi
openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -keyout "$PRODSIM_DIR/certs/prodsim.key" \
    -out "$PRODSIM_DIR/certs/prodsim.crt" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
chmod 644 "$PRODSIM_DIR/certs/prodsim.crt" "$PRODSIM_DIR/certs/prodsim.key"
devolve_ao_usuario "$PRODSIM_DIR/certs"
echo "Certificado gerado em $PRODSIM_DIR/certs."
