import pytest
from django_webtest import DjangoTestApp, WebTestMixin

# Testes que dependem de módulos removidos (scripts.lista_urls, etc.)
# ou de views/models que foram reestruturados
collect_ignore_glob = [
    "sapl/test_urls.py",
    "sapl/rules/tests/test_rules.py",
    "cmj/globalrules/tests/test_rules.py",
    "sapl/sessao/tests/test_sessao_view.py",
]


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
        except Exception:
            pass


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


class OurTestApp(DjangoTestApp):

    def __init__(self, *args, **kwargs):
        self.default_user = kwargs.pop("default_user", None)
        super(OurTestApp, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        kwargs.setdefault("user", self.default_user)
        kwargs.setdefault("auto_follow", True)
        return super(OurTestApp, self).get(*args, **kwargs)


@pytest.fixture(scope="function")
def app(request, admin_user):
    """WebTest's TestApp.

    Patch and unpatch settings before and after each test.

    WebTestMixin, when used in a unittest.TestCase, automatically calls
    _patch_settings() and _unpatchsettings.

    source: https://gist.github.com/magopian/6673250
    """
    wtm = WebTestMixin()
    wtm._patch_settings()
    request.addfinalizer(wtm._unpatch_settings)
    # XXX change this admin user to "saploper"
    return OurTestApp(default_user=admin_user.username)
