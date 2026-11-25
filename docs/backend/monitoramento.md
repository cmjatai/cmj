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
| `postgres` | postgres-exporter com `pg_stat_statements` e coletores extras (seção Postgres) |
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

### Postgres

Além dos coletores padrão, o `postgres-exporter` liga em `docker/docker-compose-monitoring.yaml`:

| Coletor | Para quê |
| --- | --- |
| `stat_statements` com `include_query` | tempo, chamadas e linhas por consulta, com o texto (até 300 caracteres) |
| `stat_checkpointer` | checkpoints e buffers escritos; no PG 17+ saíram de `pg_stat_bgwriter` |
| `database_wraparound` | idade do `datfrozenxid` e do `datminmxid` |
| `statio_user_indexes` | blocos de cada índice lidos do cache e do disco |
| `stat_activity_autovacuum` | tabelas com autovacuum em andamento |
| `postmaster` | horário do último início do Postgres |

O texto das consultas vem normalizado pelo `pg_stat_statements` (constantes viram `$1`), então não
leva dados do banco para o Prometheus. Isso vale para `SELECT`, `INSERT`, `UPDATE` e `DELETE`, mas
não para todo comando utilitário: um `CREATE ROLE ... PASSWORD '...'` poderia ir com a senha. Por
isso o Postgres roda com `pg_stat_statements.track_utility=off`, que também evita que DDL de
restore e migrations ocupe as vagas das consultas. O exporter envia só as 100 consultas de maior tempo
acumulado. O `extend.query-path` (consultas próprias em `queries.yaml`) não é usado: está
deprecated no exporter.

O Postgres roda com `track_io_timing=on` (no `command` dos três composes), que preenche os tempos de
leitura e escrita de bloco do `pg_stat_statements` e do `pg_stat_database`. Sem ele, esses painéis
ficam em zero.

Na produção, as duas configurações valem sem reiniciar o banco, antes de recriar o
`postgres-exporter` com o `include_query` (como superusuário, no banco `cmj`):

```sql
ALTER SYSTEM SET track_io_timing = on;
ALTER SYSTEM SET pg_stat_statements.track_utility = off;
SELECT pg_reload_conf();
SHOW track_io_timing;
SHOW pg_stat_statements.track_utility;
-- apaga o que já foi registrado, inclusive comandos utilitários (zera o histórico das consultas)
SELECT pg_stat_statements_reset();
```

O `command` do compose vale na próxima recriação do container e tem prioridade sobre o
`postgresql.auto.conf` gravado pelo `ALTER SYSTEM`.

O dashboard `PortalCMJ – Postgres` (`portalcmj-postgres.json`, gerado por
`docker/grafana/geradores/portalcmj_postgres.py`: altere o script e rode-o, sem editar o JSON) reúne saúde, atividade (conexões,
transações longas, locks), as consultas que mais consumiram tempo, as maiores tabelas com vacuum e
seq scans, os índices que mais leem do disco e checkpoints. O `postgres.json` da comunidade fica
como foi baixado; o painel "Buffers" dele está vazio, porque usa nomes de métrica anteriores ao
sufixo `_total` e colunas que o PG 18 não tem mais.

Os dashboards provisionados ficam na pasta PortalCMJ do Grafana e não aceitam edição pela
interface: para mudar, exporte o JSON e substitua o arquivo em `docker/grafana/dashboards/`.

## Alertas

O Grafana avalia a cada minuto as regras de `docker/grafana/provisioning/alerting/regras.yml` e
manda os avisos para o contato `portalcmj`. Alertas que disparam juntos chegam numa mensagem só;
um alerta ativo é lembrado a cada 4 horas, e outra mensagem avisa quando normaliza.

| Regra | Dispara quando | Severidade |
| --- | --- | --- |
| Site fora | nenhuma cor da aplicação responde há 2 min | crítico |
| Erros 5xx | mais de 5% das respostas são 5xx há 5 min (com tráfego acima de 0,1 req/s) | crítico |
| Disco quase cheio | menos de 15% livre num sistema de arquivos há 10 min | crítico |
| Serviço fora | exporter, Redis ou Postgres sem responder há 5 min | alto |
| Conexões do Postgres | acima de 80% de `max_connections` há 5 min | alto |
| Transação ociosa aberta no Postgres | conexão `idle in transaction` há mais de 5 min, por 5 min | alto |
| Wraparound de transações no Postgres | idade do `datfrozenxid` acima de 1 bilhão há 10 min | alto |
| Fila do Celery acumulando | mais de 200 tarefas numa fila há 15 min | alto |
| Worker do Celery fora | um worker sem responder há 5 min | alto |
| Lentidão | p95 acima de 3 s há 10 min (com tráfego acima de 0,1 req/s) | médio |
| Memória do servidor | acima de 90% há 10 min | médio |
| Transação longa no Postgres | transação em execução há mais de 30 min, por 5 min (inclui autovacuum) | médio |
| Deadlocks no Postgres | algum deadlock nos últimos 15 min | médio |
| Cache hit baixo no Postgres | menos de 95% dos blocos lidos no cache, em 30 min, por 30 min | médio |

O destino é escolhido por `GRAFANA_CONTATO` no `docker/.env`, que monta um dos arquivos de
`docker/grafana/contatos/`:

- `desligado` (padrão e dev): os alertas aparecem só em Alerting > Alert rules.
- `telegram` (produção): manda para o chat de `TELEGRAM_ALERTAS_CHAT_ID`.
- `webhook-local` (produção simulada): manda para o container `alerta-receptor`, que só mostra no
  log (`sudo docker logs prodsim-alerta-receptor`). Nada sai para a internet.

### Ligar o Telegram na produção

1. No Telegram, falar com o @BotFather, criar um bot (`/newbot`) e guardar o token.
2. Adicionar o bot como administrador do canal, com permissão de publicar mensagens.
3. Descobrir o ID do canal: publicar qualquer mensagem no canal e abrir, no navegador,
   `https://api.telegram.org/bot<token>/getUpdates`. O ID está em `channel_post.chat.id` e começa
   com `-100`.
4. No `docker/.env` do servidor:

   ```bash
   GRAFANA_CONTATO=telegram
   TELEGRAM_ALERTAS_BOT_TOKEN=<token>
   TELEGRAM_ALERTAS_CHAT_ID=<-100...>
   ```

5. Recriar só o Grafana:
   `sudo docker compose -f docker/docker-compose.yaml --env-file docker/.env up -d --no-deps --force-recreate grafana`.
6. Testar: no Grafana, Alerting > Contact points > `portalcmj` > Test. A mensagem de teste deve
   chegar ao canal.

O servidor precisa alcançar `api.telegram.org` pela internet.

Na produção simulada, para ver uma regra disparar de verdade, pare um exporter e acompanhe a regra
em Alerting > Alert rules (Pending, e Firing depois de 5 minutos):

```bash
sudo docker stop portalcmj-prodsim-redis-exporter-1
sudo docker logs prodsim-alerta-receptor 2>&1 | grep -i "Serviço fora"   # depois do Firing
sudo docker start portalcmj-prodsim-redis-exporter-1
```

A regra de disco ignora montagens de rede (`fuse.*`, como o sshfs) e as do snap.

Para mudar um limite, edite `regras.yml` e recrie o Grafana como no passo 5. As regras
provisionadas não aceitam edição pela interface.

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
