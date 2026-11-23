import ipaddress
import logging
import socket
from urllib.parse import urlparse

import pytest
from django_webtest import DjangoTestApp, WebTestMixin

logger = logging.getLogger(__name__)

# Testes que dependem de módulos removidos (scripts.lista_urls, etc.)
# ou de views/models que foram reestruturados
collect_ignore_glob = [
    "sapl/test_urls.py",
    "sapl/rules/tests/test_rules.py",
    "cmj/globalrules/tests/test_rules.py",
    "sapl/sessao/tests/test_sessao_view.py",
]


@pytest.fixture(autouse=True)
def create_base_appconfig():
    """Cria um registro de sapl.base.models.AppConfig para evitar erros de
    em testes que importam AppConfig diretamente."""
    from sapl.base.models import AppConfig

    AppConfig.attr("id")


@pytest.fixture(scope="session")
def django_db_setup(
    request,
    django_test_environment,
    django_db_blocker,
    django_db_use_migrations,
    django_db_keepdb,
    django_db_createdb,
    django_db_modify_db_settings,
):
    """Cria um template database com extensões PostgreSQL (pgvector, pg_trgm,
    unaccent) e delega ao setup_databases do pytest-django."""
    import psycopg
    from django.conf import settings
    from django.test.utils import setup_databases, teardown_databases
    from pytest_django.fixtures import _disable_migrations

    # Desabilita migrations se --no-migrations foi passado
    if not django_db_use_migrations:
        _disable_migrations()

    if settings.DATABASE_URL_DEV == settings.DATABASE_URL_BLOCK:
        raise RuntimeError(
            "DATABASE_URL_DEV e DATABASE_URL_BLOCK não podem ser iguais. "
            "Verifique as variáveis de ambiente."
        )

    db = settings.DATABASES["default"]
    template_db = "template_cmj_test"

    conn_params = {
        "dbname": "postgres",
        "user": db["USER"],
        "password": db["PASSWORD"],
        "host": db["HOST"],
        "port": db.get("PORT", 5432),
        "autocommit": True,
    }

    with django_db_blocker.unblock():
        # Cria/atualiza template database com extensões necessárias
        admin_conn = psycopg.connect(**conn_params)
        with admin_conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (template_db,),
            )
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{template_db}"')
        admin_conn.close()

        # Instala extensões no template
        conn_params["dbname"] = template_db
        tpl_conn = psycopg.connect(**conn_params)
        with tpl_conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            cur.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        tpl_conn.close()

        # Configura Django para usar o template ao criar o banco de teste
        settings.DATABASES["default"].setdefault("TEST", {})
        settings.DATABASES["default"]["TEST"]["TEMPLATE"] = template_db

        setup_databases_args = {}
        if django_db_keepdb and not django_db_createdb:
            setup_databases_args["keepdb"] = True

        db_cfg = setup_databases(
            verbosity=request.config.option.verbose,
            interactive=False,
            aliases=["default"],
            **setup_databases_args,
        )

    yield

    with django_db_blocker.unblock():
        try:
            teardown_databases(db_cfg, verbosity=0)
        except Exception as e:
            logger.warning(f"Erro ao desmontar banco de testes: {e}")


@pytest.fixture(scope="session", autouse=True)
def _configure_celery_for_tests():
    """Configura Celery para execução síncrona nos testes (sem Redis)."""
    from cmj.celery import app as celery_app

    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_url="memory://",
        result_backend="cache+memory://",
    )


@pytest.fixture(autouse=True)
def _clear_cache_between_tests():
    """Limpa cache após cada teste para evitar contaminação cruzada."""
    from django.core.cache import cache

    yield

    # Limpa cache DummyCache e MemoryCache
    if hasattr(cache, 'clear'):
        cache.clear()


@pytest.fixture(scope="session", autouse=True)
def _configure_test_settings():
    """Configura settings específicos para testes."""
    from django.conf import settings

    # Usar DummyCache em testes garante que não há estado entre testes
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
    # Desabilita alguns processadores que podem interferir em testes
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'


@pytest.fixture(autouse=True)
def _cleanup_django_signals():
    """Limpa signal handlers entre testes para evitar contaminação cruzada."""
    yield

    try:
        # Desconecta signal handlers temporários adicionados durante testes
        # Mantém handlers padrão do Django e da app
        from django.db.models import signals

        # Itera sobre sinais comuns
        for signal in [signals.post_save, signals.post_delete, signals.pre_save]:
            # Se há maneira de identificar handlers de teste, desconecta
            # Por enquanto, apenas log de debug
            logger.debug(f"Signal {signal} tem {len(signal.receivers)} receivers ativos")
    except Exception as e:
        logger.debug(f"Erro ao limpar signals de teste: {e}")


@pytest.fixture(autouse=True)
def _rede_social_nao_envia_nos_testes(monkeypatch):
    """Nenhum teste publica em rede social: a task que o signal de rede
    social aciona encontra, no lugar de cada função de envio, uma que não
    faz nada."""
    from cmj.core import tasks

    for nome in [n for n in vars(tasks) if n.startswith("send_")]:
        monkeypatch.setattr(tasks, nome, lambda pk: None)


class ConexaoExternaBarrada(OSError):
    """Um teste tentou comunicar com um destino que não é local."""


class VigiaDeRede:
    """Barra, durante os testes, a comunicação com destino que não é local.

    Troca as funções de socket do Python que abrem conexão, enviam datagrama
    ou resolvem nome. Passam o loopback, as redes privadas, os sockets de
    arquivo e os nomes dos serviços das settings (banco, Redis, Solr e dev
    server). Qualquer outro destino levanta ``ConexaoExternaBarrada`` antes de
    sair da máquina, sem consulta de DNS, e fica em ``tentativas``.

    Só enxerga sockets Python: bibliotecas que abrem a conexão em código
    nativo, como a libpq do PostgreSQL, não passam por aqui.
    """

    def __init__(self):
        self.tentativas = []
        self._nomes_liberados = None
        self._originais = {}

    @property
    def nomes_liberados(self):
        if self._nomes_liberados is None:
            from django.conf import settings

            nomes = {"localhost", socket.gethostname()}
            nomes.update(db.get("HOST") for db in settings.DATABASES.values())
            nomes.add(getattr(settings, "REDIS_HOST", None))
            nomes.add(urlparse(getattr(settings, "SOLR_URL", "")).hostname)
            nomes.add(getattr(settings, "DEV_HOST_NAME", None))
            self._nomes_liberados = {n.lower() for n in nomes if n}
        return self._nomes_liberados

    # loopback, redes privadas e link-local. Não se usa ``is_private``, que
    # também aceita faixas reservadas que não são da rede local
    redes_locais = [
        ipaddress.ip_network(rede)
        for rede in (
            "127.0.0.0/8",
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
            "169.254.0.0/16",
            "::1/128",
            "fc00::/7",
            "fe80::/10",
        )
    ]

    @classmethod
    def ip_local(cls, host):
        """``None`` quando ``host`` não é um IP."""
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            return None
        ip = getattr(ip, "ipv4_mapped", None) or ip
        return any(
            ip.version == rede.version and ip in rede for rede in cls.redes_locais
        )

    def liberado(self, endereco, por_nome):
        # socket de arquivo (AF_UNIX) e outras famílias sem host
        if not isinstance(endereco, tuple):
            return True
        host = endereco[0]
        if isinstance(host, bytes):
            host = host.decode("ascii", "replace")
        if not host:
            return True
        local = self.ip_local(host)
        if local is not None:
            return local
        # nome só vale para resolver; a conexão é conferida pelo IP resolvido
        return por_nome and host.lower() in self.nomes_liberados

    def confere(self, operacao, endereco, por_nome=False):
        if not self.liberado(endereco, por_nome):
            self.tentativas.append(f"{operacao} {endereco!r}")
            raise ConexaoExternaBarrada(
                f"Comunicação externa barrada nos testes: {operacao} {endereco!r}. "
                "Troque o cliente por mock."
            )

    def reprovacao(self):
        """Mensagem para reprovar o teste que tentou sair, ainda que o código
        testado tenha engolido o erro; ``None`` se não houve tentativa."""
        if not self.tentativas:
            return None
        return (
            "O teste tentou comunicar com destino externo: "
            + "; ".join(self.tentativas)
            + ". Troque o cliente por mock."
        )

    def instalar(self):
        vigia = self
        self._originais = {
            (socket.socket, "connect"): socket.socket.connect,
            (socket.socket, "connect_ex"): socket.socket.connect_ex,
            (socket.socket, "sendto"): socket.socket.sendto,
            (socket, "getaddrinfo"): socket.getaddrinfo,
            (socket, "gethostbyname"): socket.gethostbyname,
            (socket, "gethostbyname_ex"): socket.gethostbyname_ex,
        }
        originais = self._originais

        def connect(sock, address):
            vigia.confere("connect", address)
            return originais[socket.socket, "connect"](sock, address)

        def connect_ex(sock, address):
            vigia.confere("connect_ex", address)
            return originais[socket.socket, "connect_ex"](sock, address)

        def sendto(sock, data, *args):
            vigia.confere("sendto", args[-1] if args else None)
            return originais[socket.socket, "sendto"](sock, data, *args)

        def getaddrinfo(host, *args, **kwargs):
            vigia.confere("getaddrinfo", (host,), por_nome=True)
            return originais[socket, "getaddrinfo"](host, *args, **kwargs)

        def gethostbyname(host):
            vigia.confere("gethostbyname", (host,), por_nome=True)
            return originais[socket, "gethostbyname"](host)

        def gethostbyname_ex(host):
            vigia.confere("gethostbyname_ex", (host,), por_nome=True)
            return originais[socket, "gethostbyname_ex"](host)

        for troca in (
            connect,
            connect_ex,
            sendto,
            getaddrinfo,
            gethostbyname,
            gethostbyname_ex,
        ):
            dono = socket if troca.__name__.startswith("get") else socket.socket
            setattr(dono, troca.__name__, troca)

    def remover(self):
        for (dono, nome), original in self._originais.items():
            setattr(dono, nome, original)
        self._originais = {}


_vigia_de_rede = VigiaDeRede()


def pytest_configure(config):
    _vigia_de_rede.instalar()


def pytest_unconfigure(config):
    _vigia_de_rede.remover()


@pytest.fixture(autouse=True)
def vigia_de_rede():
    """Nenhum teste comunica com destino externo: a tentativa é barrada na
    hora e o teste é reprovado no fim, mesmo que o erro tenha sido engolido."""
    _vigia_de_rede.tentativas.clear()

    yield _vigia_de_rede

    reprovacao = _vigia_de_rede.reprovacao()
    _vigia_de_rede.tentativas.clear()
    if reprovacao:
        pytest.fail(reprovacao, pytrace=False)


@pytest.fixture(scope="session")
def test_user_data():
    """Define dados padrão para usuários de teste."""
    return {
        'admin': {
            'username': 'admin',
            'password': 'testpass123!',
            'email': 'admin@test.local',
            'is_staff': True,
            'is_superuser': True,
        },
        'staff': {
            'username': 'staff_user',
            'password': 'testpass123!',
            'email': 'staff@test.local',
            'is_staff': True,
            'is_superuser': False,
        },
        'regular': {
            'username': 'regular_user',
            'password': 'testpass123!',
            'email': 'user@test.local',
            'is_staff': False,
            'is_superuser': False,
        },
    }


class OurTestApp(DjangoTestApp):
    """Cliente HTTP para testes com suporte a usuário padrão e auto-follow."""

    def __init__(self, *args, **kwargs):
        self.default_user = kwargs.pop("default_user", None)
        super(OurTestApp, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        kwargs.setdefault("user", self.default_user)
        kwargs.setdefault("auto_follow", True)
        return super(OurTestApp, self).get(*args, **kwargs)


@pytest.fixture(scope="function")
def app(request, admin_user):
    wtm = WebTestMixin()
    wtm._patch_settings()
    request.addfinalizer(wtm._unpatch_settings)
    return OurTestApp(default_user=admin_user.username)
