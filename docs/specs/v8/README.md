# V8: frontend híbrido

Specs do frontend v8, uma por capacidade. O objetivo de longo prazo do v8 é substituir o v6 e o
v2018. Marcadores, IDs, ligação com testes e varredura de segurança seguem
[`docs/specs/README.md`](../README.md).

| Spec | Prefixo | Assunto |
| --- | --- | --- |
| [arquitetura.md](./arquitetura.md) | `V8-ARQ` | App `cmj/v8`, rotas, templates base e layouts, dados globais, app Vue único, ilhas e zonas SPA |
| [shell.md](./shell.md) | `V8-SHELL` | Topbar, sidebar, breadcrumbs, menu por permissão, cache, tema claro e escuro |
| [overlays.md](./overlays.md) | `V8-OVL` | Camadas, pilha, drawers, modals, toasts, gatilhos em HTML, fragmentos do servidor |
| [http.md](./http.md) | `V8-HTTP` | Cliente HTTP, CSRF, sessão expirada, formato de erro |
| [demo.md](./demo.md) | `V8-DEMO` | Páginas de demonstração dos dois modos |

## Os dois modos de tela

| Modo | Quem renderiza | Onde o Vue entra | Drawer na URL |
| --- | --- | --- | --- |
| Página Django com ilhas | Django, com template e contexto | Em cada `[data-vue-island]` | Query string `?painel=` |
| Zona SPA | Django entrega o shell; o Vue Router cuida do miolo | Em `[data-vue-zone]` | Rota aninhada |

Nos dois modos a página tem um único app Vue, um único Pinia e uma única pilha de overlays.

## Limites que valem para todas as specs

- Tudo o que o v8 cria responde em `/v8/...`.
- Os únicos arquivos existentes alterados fora de `_frontend/v8` e `_templates/v8` estão listados no
  Escopo de `arquitetura.md`.
- `_frontend/v6`, `_frontend/v2018`, `_templates/v6`, `_templates/v2018` e os apps existentes não
  recebem migração nem funcionalidade nova.

## Testes

- Django: `python -m pytest cmj/v8`. Cada teste aponta a regra com `@pytest.mark.spec("<ID>")`.
- Frontend: `cd _frontend/v8 && npm run test`. O ID da regra abre o nome do teste, como em
  `it('V8-OVL-011: ESC fecha só o topo da pilha', ...)`. Usa Vitest, `@vue/test-utils` e jsdom.
