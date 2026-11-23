import ipaddress
import logging

from django.http import HttpResponseForbidden

# Loopback e redes privadas: as mesmas faixas do allow do nginx do container
# (docker/nginx/cmj_docker.conf), de onde vêm o Prometheus e os healthchecks.
ALLOWED_IPS = [
    "127.0.0.1",
    "::1",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "fc00::/7",
]

# As rotas de saúde e versão têm barra final em cmj/urls.py; as formas sem
# barra ficam na lista para que nenhuma das duas escape da checagem.
RESTRICTED_ENDPOINTS = [
    "/metrics",
    "/health/",
    "/ready/",
    "/version/",
    "/health",
    "/ready",
    "/version",
]

logger = logging.getLogger(__name__)


def ip_do_cliente(request):
    """IP usado para liberar os endpoints restritos.

    Lê o X-Real-IP, que o nginx do container sempre reescreve com o IP do
    cliente (após o real_ip). Não usa o X-Forwarded-For: o proxy da frente o
    repassa com $proxy_add_x_forwarded_for, e o primeiro elemento é o que o
    próprio cliente enviou. Sem o X-Real-IP (runserver, por exemplo), vale o
    REMOTE_ADDR.
    """
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")


class EndpointRestrictionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # IP do cliente
        # bloqueia acesso a endpoints restritos para IPs nao permitidos
        if request.path in RESTRICTED_ENDPOINTS:
            client_ip = ip_do_cliente(request)

            try:
                for allowed_ip in ALLOWED_IPS:
                    if ipaddress.ip_address(client_ip) in ipaddress.ip_network(
                        allowed_ip
                    ):
                        break
                else:
                    logger.warning(
                        f"Acesso proibido ao endpoint {request.path} para o IP {client_ip}"
                    )
                    return HttpResponseForbidden("Acesso proibido")
            except ValueError:
                logger.error(f"IP inválido: {client_ip}")
                return HttpResponseForbidden("Acesso proibido")

        return self.get_response(request)
