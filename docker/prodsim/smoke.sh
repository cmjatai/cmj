#!/usr/bin/env bash
# Verificações da produção simulada, sempre em localhost.
# Uso: sudo docker/prodsim/smoke.sh
source "$(dirname "$0")/_comum.sh"
set +e

BASE="https://localhost:${PRODSIM_HTTPS_PORT}"
PROM="http://127.0.0.1:${PROMETHEUS_PORT}"
GRAF="http://127.0.0.1:${GRAFANA_PORT}"
for u in "$BASE" "$PROM" "$GRAF"; do exige_localhost "$u"; done

# Cliente da internet simulado (ver X-Simula-IP-Cliente em nginx-front.conf).
IP_PUBLICO="200.150.10.20"

OK=0; FALHA=0
passa() { echo "  ok    $1"; OK=$((OK + 1)); }
falha() { echo "  FALHA $1"; FALHA=$((FALHA + 1)); }
status() { curl -sk -o /dev/null -w '%{http_code}' --max-time 30 "$@"; }
confere() { # descrição, esperado (regex), comando curl...
    local desc="$1" esperado="$2"; shift 2
    local s; s="$(status "$@")"
    if [[ "$s" =~ ^($esperado)$ ]]; then passa "$desc ($s)"; else falha "$desc: veio $s, esperado $esperado"; fi
}

# O start.sh só sobe o nginx do container depois do migrate, do Solr e do
# Celery: até lá o front responde 502. Espera até ESPERA segundos.
ESPERA="${ESPERA:-300}"
inicio=$SECONDS
until [[ "$(status "$BASE/robots.txt")" == "200" ]]; do
    if (( SECONDS - inicio >= ESPERA )); then
        echo "A aplicação não respondeu em ${ESPERA}s. Veja: sudo docker logs --tail 50 prodsim-cmj-blue"
        exit 1
    fi
    echo "  aguardando a aplicação subir ($(( SECONDS - inicio ))s)..."
    sleep 5
done

echo "Portal pelo nginx da frente ($BASE)"
confere "home" "200|30[12]" "$BASE/"
confere "http redireciona para https" "301" "http://localhost:${PRODSIM_HTTP_PORT}/"
confere "estático (robots.txt)" "200" "$BASE/robots.txt"
confere "API pública" "200" "$BASE/api/sessao/sessaoplenaria/?page_size=1"
confere "WebSocket /ws/sync/" "101" --http1.1 --max-time 3 \
    -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" \
    -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" -H "Origin: $BASE" "$BASE/ws/sync/"
confere "parâmetro u cai no 444" "000" "$BASE/?u=teste"
confere "extensão .php cai no 444" "000" "$BASE/index.php"

echo "Endpoints restritos"
for p in metrics health/ ready/ version/ health ready version; do
    confere "/$p de IP público é negado" "403" -H "X-Simula-IP-Cliente: $IP_PUBLICO" "$BASE/$p"
    confere "/$p de IP público com X-Forwarded-For de loopback é negado" "403" \
        -H "X-Simula-IP-Cliente: $IP_PUBLICO" -H "X-Forwarded-For: 127.0.0.1" "$BASE/$p"
done
confere "/metrics da rede privada é liberado" "200" "$BASE/metrics"
confere "/health/ da rede privada responde" "200" "$BASE/health/"
confere "/version/ da rede privada responde" "200" "$BASE/version/"
confere "/nginx_status de IP público é negado" "403" -H "X-Simula-IP-Cliente: $IP_PUBLICO" "$BASE/nginx_status"

echo "Métricas somadas entre os workers do gunicorn (modo multiprocess)"
soma() {
    curl -sk --max-time 30 "$BASE/metrics" \
        | awk '/^django_http_requests_total_by_transport_total\{/ {s += $2} END {printf "%d", s}'
}
anterior="$(soma)"; cresce=1
for _ in 1 2 3 4 5 6 7 8; do
    atual="$(soma)"
    [ "$atual" -ge "$anterior" ] || cresce=0
    anterior="$atual"
done
if [ "$cresce" = 1 ] && [ "$anterior" -gt 0 ]; then
    passa "contador não diminui entre coletas (total $anterior)"
else
    falha "contador oscilou entre coletas ou veio zerado (último $anterior)"
fi

echo "Log que o fail2ban leria (só respostas que não são 1xx, 2xx nem 3xx)"
indevidas="$(docker exec prodsim-front sh -c 'cat /var/log/nginx/front_error_requests.log 2>/dev/null' \
    | grep -cE '" [123][0-9]{2} ' || true)"
if [ "${indevidas:-0}" = 0 ]; then passa "nenhuma 1xx, 2xx ou 3xx no log de erros"; else falha "$indevidas linhas 1xx, 2xx ou 3xx no log de erros"; fi

echo "Monitoramento"
confere "Grafana /api/health" "200" "$GRAF/api/health"
confere "Prometheus pronto" "200" "$PROM/-/ready"
GREEN=0; container_rodando prodsim-cmj-green && GREEN=1
ALVOS="$(curl -s --max-time 10 "$PROM/api/v1/targets?state=active" | GREEN="$GREEN" python3 -c '
import json, os, sys
green = os.environ["GREEN"] == "1"
for a in json.load(sys.stdin)["data"]["activeTargets"]:
    nome = "%s %s" % (a["labels"]["job"], a["labels"]["instance"])
    if a["health"] == "up":
        print("  ok    alvo " + nome)
    elif not green and "green" in a["labels"]["instance"]:
        print("  -     alvo %s fora do ar (green desligado)" % nome)
    else:
        print("  FALHA alvo %s: %s" % (nome, a.get("lastError", "")))
')"
echo "$ALVOS"
if [ -z "$ALVOS" ]; then
    falha "não consegui ler os alvos do Prometheus"
elif grep -q "FALHA" <<< "$ALVOS"; then
    falha "há alvos do Prometheus fora do ar"
else
    passa "alvos do Prometheus"
fi

echo "Alertas do Grafana"
GAUTH=(-u "admin:${GRAFANA_ADMIN_PASSWORD}")
regras="$(curl -s --max-time 10 "${GAUTH[@]}" "$GRAF/api/v1/provisioning/alert-rules" \
    | python3 -c 'import json,sys; print(len([r for r in json.load(sys.stdin) if r.get("uid","").startswith("portalcmj-")]))' 2>/dev/null)"
if [ "${regras:-0}" = 9 ]; then passa "9 regras de alerta carregadas"; else falha "regras de alerta carregadas: ${regras:-0} (esperado 9)"; fi

url_contato="$(curl -s --max-time 10 "${GAUTH[@]}" "$GRAF/api/v1/provisioning/contact-points?name=portalcmj" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["settings"].get("url",""))' 2>/dev/null)"
if [ "$url_contato" = "http://alerta-receptor:8080/alertas" ]; then
    passa "contato portalcmj com a variável de ambiente expandida"
else
    falha "contato portalcmj com url '$url_contato' (esperado http://alerta-receptor:8080/alertas)"
fi

teste="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "${GAUTH[@]}" -H 'Content-Type: application/json' \
    -X POST "$GRAF/api/alertmanager/grafana/config/api/v1/receivers/test" \
    -d '{"receivers":[{"name":"teste","grafana_managed_receiver_configs":[{"uid":"","name":"teste","type":"webhook","disableResolveMessage":false,"settings":{"url":"http://alerta-receptor:8080/alertas"},"secureFields":{}}]}]}')"
sleep 2
if [ "$teste" = 200 ] && docker logs prodsim-alerta-receptor 2>&1 | grep -q '/alertas'; then
    passa "notificação de teste chegou ao alerta-receptor"
else
    falha "notificação de teste: HTTP $teste; veja sudo docker logs prodsim-alerta-receptor"
fi

echo
echo "Resultado: $OK ok, $FALHA falha(s)"
[ "$FALHA" = 0 ]
