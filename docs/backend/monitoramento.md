# Monitoramento e produção simulada

## Arquitetura

| Arquivo | Papel |
| --- | --- |
| `docker/docker-compose-monitoring.yaml` | Prometheus, Grafana e exporters; incluído (`include:`) pelo compose da produção e pelo da produção simulada |
| `docker/prometheus/prometheus.yml` | Alvos da produção e da simulação (nomes de container, iguais nos dois) |
| `docker/prometheus/prometheus-dev.yml` | Alvos do dev: `cmj:9000` e o runserver do host em `9098` |
| `docker/grafana/provisioning/` | Datasource `prometheus` (uid fixo) e provider dos dashboards |
| `docker/grafana/dashboards/` | Dashboards versionados (origem de cada um no `README.md` da pasta) |
| `docker/.env.example` | Modelo do `docker/.env` do servidor, que não é versionado |

O que é coletado:

| Job | Origem |
| --- | --- |
| `django` | `/metrics` do `django_prometheus` em `cmj-blue:80` e `cmj-green:80` (label `color`) |
| `nginx` | `/nginx_status` do nginx de cada container, via `nginx-exporter-blue/green` |
| `node` | node-exporter: CPU, memória, disco e carga do servidor |
| `cadvisor` | consumo de cada container |
| `postgres` | postgres-exporter com `pg_stat_statements` |
| `redis` | redis-exporter |
| `celery` | celery-exporter, que lê os eventos de tarefa no broker |
| `solr` | `solr-exporter` da imagem do Solr 9.5, pelo ZooKeeper embutido |

O dev só tem Prometheus e Grafana, sem exporters, publicados em `127.0.0.1:9090` e
`127.0.0.1:3000` (Grafana: admin/admin).

### Métricas da aplicação

- O gunicorn roda com `PROMETHEUS_MULTIPROC_DIR=/var/cmjatai/cmj/run/prometheus`
  (`docker/start_gunicorn.sh`): cada worker grava em arquivo e o `/metrics` soma todos.
  `docker/gunicorn.conf.py` marca o worker como morto ao sair. O diretório é limpo quando o
  gunicorn sobe. Os arquivos dos workers reciclados pelo `--max-requests` se acumulam até lá; o
  painel "Duração da coleta do /metrics" mostra o efeito.
- Nesse modo não saem `python_info` nem `process_*`: o consumo do processo vem do cAdvisor.
- Daphne, Celery e `manage.py` não usam o diretório.
- Os workers do Celery enviam eventos de tarefa (`CELERY_WORKER_SEND_TASK_EVENTS` e
  `CELERY_TASK_SEND_SENT_EVENT`).

### Acesso aos endpoints de operação

`/metrics`, `/health/`, `/ready/`, `/version/` e `/nginx_status` só respondem a loopback e redes
privadas, em duas camadas:

1. O nginx do container (`docker/nginx/cmj_docker.conf`), com `allow`/`deny` sobre o
   `$remote_addr` já resolvido pelo `real_ip`.
2. `EndpointRestrictionMiddleware` (`cmj/middleware/endpoint_restriction.py`), que decide pelo
   `X-Real-IP`. Não use o `X-Forwarded-For` para isso: o proxy da frente o repassa com
   `$proxy_add_x_forwarded_for`, e o primeiro elemento é o que o cliente enviou.

## Produção

Só o Grafana pode sair do loopback, no IP da rede interna do servidor, definido no `docker/.env`.
O Prometheus fica em `127.0.0.1:9090` (acesso por túnel SSH: `ssh -L 9090:127.0.0.1:9090
<servidor>`), e os exporters não publicam porta.

O compose da produção não sobe sem o `docker/.env`: faltam `GRAFANA_ADMIN_PASSWORD` e
`PG_EXPORTER_DSN`.

### Primeira subida no servidor

1. `docker compose version` precisa ser 2.20 ou mais recente (`include:`).
2. Criar `docker/.env` a partir de `docker/.env.example`, com o IP interno em
   `MONITORING_BIND_IP`. Conferir antes que esse IP não é alcançável pela internet.
3. Criar o usuário do postgres-exporter no Postgres da produção:

   ```sql
   CREATE ROLE monitor LOGIN PASSWORD '...';
   GRANT pg_monitor TO monitor;
   CREATE EXTENSION IF NOT EXISTS pg_stat_statements;  -- no banco cmj
   ```

4. Subir só o monitoramento, sem tocar na aplicação nem em Postgres, Redis e Solr:

   ```bash
   sudo docker compose -f docker/docker-compose.yaml up -d --no-deps prometheus grafana \
     node-exporter cadvisor postgres-exporter redis-exporter celery-exporter \
     nginx-exporter-blue nginx-exporter-green solr-exporter
   ```

   Os containers `prometheus` e `grafana` antigos são recriados com o nome do compose
   (`portalcmj-prometheus-1`...). Os volumes `portalcmj_prometheus_data` e `portalcmj_grafana_data`
   são os mesmos.
5. O volume do Grafana já existe, então a senha do `docker/.env` não é aplicada. Trocar com:
   `sudo docker compose -f docker/docker-compose.yaml exec grafana grafana cli admin reset-admin-password '<senha>'`.
6. Fazer o deploy da aplicação pelo fluxo blue/green do servidor, que sobe a cor parada, troca o
   upstream do proxy do host e para a outra. Não suba `cmj-blue` e `cmj-green` juntos com
   `up -d`: cada um roda o Celery beat, e as tarefas periódicas sairiam em dobro.
7. Conferir em `http://127.0.0.1:9090/targets` (pelo túnel) que os alvos estão `UP`. O job
   `django` da cor parada fica sempre fora do ar; o painel "Cores da aplicação no ar" mostra 1
   fora de um deploy.

Os dashboards provisionados ficam na pasta PortalCMJ do Grafana e não aceitam edição pela
interface: para mudar, exporte o JSON e substitua o arquivo em `docker/grafana/dashboards/`.

## Produção simulada

`docker/docker-compose-dev-mode-prod.yaml`: a imagem da produção (`docker/Dockerfile`), com
`DEBUG=False`, gunicorn, daphne, Celery, nginx do container e a mesma stack de monitoramento. Tudo
em localhost.

- Projeto `portalcmj-prodsim`, isolado do dev: rede `prodsim-net` e Postgres, Redis e Solr
  próprios, com os nomes de serviço da produção (`cmjdb18`, `cmjredis`, `cmjsolr`). Pode subir
  junto com o dev.
- Um nginx (`front`) faz o papel do proxy do host: TLS autoassinado, `X-Real-IP`,
  `$proxy_add_x_forwarded_for`, 444 e o log `front_error_requests.log` com as respostas que não são
  1xx, 2xx nem 3xx, que é o que o fail2ban lê na produção. Só na simulação, o cabeçalho
  `X-Simula-IP-Cliente` troca o IP do cliente, para testar como cliente da internet.
- O `.env` da aplicação é `docker/prodsim/cmj.env`, criado pelo `up.sh` a partir do
  `cmj.env.example`. Não ponha nele chave de serviço externo.

| Serviço | Endereço |
| --- | --- |
| Portal | `https://localhost:8443` (e `http://localhost:8088`, que redireciona) |
| Grafana | `http://127.0.0.1:3001` (admin/admin) |
| Prometheus | `http://127.0.0.1:9091` |

Scripts (com `sudo`, porque usam o docker). Todos recusam alvo fora de localhost:

```bash
sudo docker/prodsim/up.sh             # gera certificado e cmj.env se faltarem, build e up
sudo docker/prodsim/up.sh --green     # com o cmj-green também
sudo docker/prodsim/db-from-dev.sh    # APAGA o banco da simulação e copia o do dev (pede confirmação)
sudo docker/prodsim/smoke.sh          # verificações de ponta a ponta
sudo docker/prodsim/down.sh           # para; --volumes apaga os dados da simulação
```

O `db-from-dev.sh` precisa do `cmjpostgres18` do dev rodando. O índice do Solr da simulação começa
vazio; o script mostra o comando de reindexação.

O `smoke.sh` confere: home, estático, API e WebSocket pelo front; o 444; `/metrics`, `/health`,
`/ready`, `/version` e `/nginx_status` negados para IP público, mesmo com `X-Forwarded-For`
forjado; o contador de requisições que não diminui entre coletas (modo multiprocess); nenhuma
resposta 1xx, 2xx ou 3xx no log do fail2ban; Grafana e Prometheus no ar e todos os alvos `UP`
(os do green só contam com `--green`).
