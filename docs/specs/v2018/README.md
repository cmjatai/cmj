# V2018: frontend em manutenção

Specs do frontend v2018 (`_frontend/v2018`), uma por capacidade. O v2018 está em manutenção, mas
continua em uso a médio e longo prazo. Marcadores, IDs, ligação com testes e varredura de segurança
seguem [`docs/specs/README.md`](../README.md).

| Spec | Prefixo | Assunto |
| --- | --- | --- |
| [estrutura.md](./estrutura.md) | `V2018-EST` | Projeto webpack, entradas, integração com o Django, aplicação principal e módulos independentes |
| [testes.md](./testes.md) | `V2018-TST` | Infraestrutura de testes: Vitest, ambiente, organização, CI |

As duas specs descrevem a estrutura. O que cada módulo faz e as regras de negócio dele ficam nas
specs do domínio, como `docs/specs/loa/`.

## Testes

`cd _frontend/v2018 && npm test`. O ID da regra abre o nome do teste, como em
`it('V2018-EST-033: só store__sync tem namespace', ...)`. Usa Vitest, `@vue/test-utils` 1 e jsdom.
