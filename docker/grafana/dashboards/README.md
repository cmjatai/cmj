# Dashboards do Grafana

Carregados pelo provisioning (`docker/grafana/provisioning/dashboards/portalcmj.yml`) na pasta
PortalCMJ. A datasource é a `prometheus` (uid fixo).

| Arquivo | Origem |
| --- | --- |
| `portalcmj-visao-geral.json` | próprio do projeto |
| `portalcmj-postgres.json` | próprio do projeto, gerado por `docker/grafana/geradores/portalcmj_postgres.py` |
| `node-exporter-full.json` | grafana.com/dashboards/1860 |
| `cadvisor.json` | grafana.com/dashboards/14282 |
| `postgres.json` | grafana.com/dashboards/14114 |
| `redis.json` | grafana.com/dashboards/763 |
| `celery.json` | grafana.com/dashboards/17509 |
| `nginx.json` | grafana.com/dashboards/12708 |
| `solr.json` | grafana.com/dashboards/12456 |
| `django.json` | grafana.com/dashboards/17658 (variável `application` lida de `django_http_requests_total_by_transport_total`, porque o modo multiprocess não exporta `python_info`) |

Os da comunidade foram baixados em 2026-11 com `${DS_*}` trocado pelo uid `prometheus`. Labels
que eles esperam (`app`, `namespace`, `cluster`) são acrescentados nos jobs de
`docker/prometheus/prometheus.yml`.
