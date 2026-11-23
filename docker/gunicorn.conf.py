# Configuração do gunicorn da produção (carregada por start_gunicorn.sh com -c).
#
# As métricas do django_prometheus usam o modo multiprocess do
# prometheus_client: cada worker grava seus valores em arquivos no diretório
# de PROMETHEUS_MULTIPROC_DIR, e o /metrics soma todos. Ao sair, o worker é
# marcado como morto para que seus gauges "live*" deixem de contar.
import os


def child_exit(server, worker):
    if not os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        return
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(worker.pid)
