# Infra: acesso aos endpoints de operação

Status: implementado (INFRA-OPS-001 a 004 e 006 a 008), acordado (009) e observado (005)
Última verificação: 2026-11-23 (branch `monitoramento-prometheus-grafana`, sobre o commit `cabdc13b6`)
Código principal: `cmj/middleware/endpoint_restriction.py`, `docker/nginx/cmj_docker.conf`,
`cmj/urls.py`, `cmj/api/views_health.py`
Testes: `cmj/middleware/tests/test_endpoint_restriction.py`

Os endpoints de operação (métricas do Prometheus, saúde e versão da aplicação e status do nginx)
deveriam responder só para loopback e redes privadas: o Prometheus e os healthchecks na rede do
docker. A restrição tem duas camadas: o nginx do container e o `EndpointRestrictionMiddleware`.

## Escopo

`/metrics` (`django_prometheus`), `/health/`, `/ready/` e `/version/` (`cmj/api/views_health.py`) e
`/nginx_status` (só no nginx do container). O proxy da frente, no host da produção, fica fora do
repositório e fora desta spec.

## Regras

- INFRA-OPS-001 [implementado] O `EndpointRestrictionMiddleware` decide pelo IP do cabeçalho
  `X-Real-IP` e, sem ele, pelo `REMOTE_ADDR`. Responde 403 quando o IP não está em nenhuma faixa de
  `ALLOWED_IPS`, e deixa passar quando está. Evidência:
  `cmj/middleware/endpoint_restriction.py:32-41`, `cmj/middleware/endpoint_restriction.py:52-65`,
  `cmj/settings/middleware.py:9`.
- INFRA-OPS-002 [implementado] O `X-Forwarded-For` não entra na decisão. O proxy da frente o repassa
  com `$proxy_add_x_forwarded_for`, e o nginx do container sempre reescreve o `X-Real-IP` com o
  endereço resolvido pelo `real_ip`. Evidência: `cmj/middleware/endpoint_restriction.py:41`,
  `docker/nginx/cmj_docker.conf:17-26`.
- INFRA-OPS-003 [implementado] IP que não é um endereço válido, ou ausente, recebe 403. Evidência:
  `cmj/middleware/endpoint_restriction.py:66-68`.
- INFRA-OPS-004 [implementado] O middleware compara `request.path` de forma exata com
  `RESTRICTED_ENDPOINTS`: `/metrics` e as rotas de saúde e versão com e sem barra final. Qualquer
  outro caminho segue sem checagem. Evidência: `cmj/middleware/endpoint_restriction.py:19-27`,
  `cmj/middleware/endpoint_restriction.py:52`.
- INFRA-OPS-005 [observado] O nginx do container repete a restrição com `allow` para as mesmas
  faixas de `ALLOWED_IPS` e `deny all` em `/metrics`, em `/health`, `/ready` e `/version` (com ou
  sem barra final) e em `/nginx_status`, sem `access_log`. Evidência:
  `docker/nginx/cmj_docker.conf:86-96`, `docker/nginx/cmj_docker.conf:98-108`.
- INFRA-OPS-006 [implementado] As rotas reais, `/metrics`, `/health/`, `/ready/` e `/version/`,
  respondem 403 a IP público. Evidência: `cmj/urls.py:98-101`,
  `cmj/middleware/endpoint_restriction.py:19-27`.
- INFRA-OPS-007 [implementado] `/health/`, `/ready/` e `/version/` informam a versão de
  `PORTALCMJ_VERSION` e, para a rede privada, `/health/` e `/version/` respondem 200 (`/ready/`
  responde 503 quando o banco ou o cache falham). Evidência: `cmj/api/views_health.py:39`,
  `cmj/api/views_health.py:81`, `cmj/api/views_health.py:113`, `cmj/settings/project.py:86`.
- INFRA-OPS-008 [implementado] `ALLOWED_IPS` aceita só loopback (`127.0.0.1` e `::1`) e as redes
  privadas `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` e `fc00::/7`. Evidência:
  `cmj/middleware/endpoint_restriction.py:8-15`.
- INFRA-OPS-009 [acordado] Sem o nginx do container na frente (runserver do dev, por exemplo), o
  `X-Real-IP` vem do próprio cliente. Fica assim: na produção e na produção simulada o nginx do
  container está sempre na frente e reescreve o cabeçalho. Evidência:
  `cmj/middleware/endpoint_restriction.py:41`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7 (2026-11-23).

## Dúvidas

Nenhuma em aberto.

## Fora do escopo

- O proxy da frente da produção e o fail2ban.
- O conteúdo das métricas e a coleta do Prometheus (`docs/backend/monitoramento.md`).
