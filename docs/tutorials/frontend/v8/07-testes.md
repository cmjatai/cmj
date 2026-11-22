# 07. Testes

Você conferiu cada passo olhando a tela. Isso não basta: daqui a um mês alguém muda uma linha e a
tela quebra sem ninguém ver. Um teste automático é um programa pequeno que usa o seu código e
confere o resultado. Ele roda em segundos, quantas vezes for preciso.

O v8 tem testes dos dois lados, com ferramentas diferentes:

| Lado | Ferramenta | Onde ficam |
| --- | --- | --- |
| Django (Python) | pytest | `cmj/v8/tests/` |
| Vue (JavaScript) | Vitest | `_frontend/v8/tests/` |

## Parte A: o lado Django

Crie `cmj/v8/tests/test_estudo.py`:

```python
"""Testes do exemplo do tutorial (docs/tutorials/frontend/v8)."""

import pytest

from cmj.v8.services import s_estudo
from cmj.v8.tests.conftest import cliente_http, html_de, ler_json_script

pytestmark = pytest.mark.django_db


def test_servico_filtra_por_autor_sem_diferenciar_maiusculas():
    assert len(s_estudo.listar()) == 3
    assert [livro["titulo"] for livro in s_estudo.listar("clarice")] == [
        "A Hora da Estrela"
    ]
    assert s_estudo.listar("ninguém") == []


def test_pagina_exige_login():
    resposta = cliente_http().get("/v8/estudo/livros/")
    assert resposta.status_code == 302
    assert resposta["Location"] == "/login/?next=/v8/estudo/livros/"


def test_pagina_lista_os_livros_e_entrega_as_props_da_ilha(comum):
    resposta = cliente_http(comum).get("/v8/estudo/livros/?autor=machado")
    html = html_de(resposta)
    assert resposta.status_code == 200
    assert "Dom Casmurro" in html and "Vidas Secas" not in html
    assert '<div data-vue-island="estudo-livros" data-props-id="v8-island-1">' in html
    assert ler_json_script(html, "v8-island-1") == {
        "livros": [
            {"id": 1, "titulo": "Dom Casmurro", "autor": "Machado de Assis", "lido": True}
        ]
    }


def test_fragmento_e_api_respondem_para_quem_esta_logado(comum):
    cliente = cliente_http(comum)
    fragmento = html_de(cliente.get("/v8/_frag/estudo/livro/2/"))
    assert "<h2 data-overlay-title>Vidas Secas</h2>" in fragmento
    assert "<html" not in fragmento
    assert cliente.get("/v8/_frag/estudo/livro/99/").status_code == 404
    assert len(cliente.get("/v8/estudo/api/livros/").json()["itens"]) == 3
```

Como ler:

- Cada função que começa com `test_` é um teste. O nome diz o que se espera, em português.
- `assert` afirma algo. Se a afirmação for falsa, o teste falha e mostra os dois valores.
- O primeiro teste chama o serviço direto, sem navegador nem página. É o mais rápido e o mais
  simples, e é por isso que a regra fica no serviço.
- `cliente_http()` é um navegador de mentira. `cliente_http(comum)` é o mesmo navegador com um
  usuário logado. Ele faz o pedido passando por rota, view e template, sem precisar de servidor no
  ar.
- `comum`, no parâmetro do teste, é uma **fixture**: o pytest vê o nome e entrega um usuário comum
  pronto. As fixtures do v8 estão em `cmj/v8/tests/conftest.py`. Há também `superusuario`.
- O segundo teste confere a proteção: sem login, a resposta é um redirecionamento (status 302) para
  a tela de login.
- O terceiro confere o HTML que o Django desenhou e os dados entregues à ilha.
- `pytestmark = pytest.mark.django_db` libera o banco para os testes do arquivo. Neste projeto
  todo teste precisa disso, mesmo o que não usa o banco.

Rode só o seu arquivo, com o virtualenv do projeto ativo:

```bash
python -m pytest cmj/v8/tests/test_estudo.py
```

Devem passar os quatro. Agora quebre algo de propósito: troque `"A Hora da Estrela"` por outro
título em `s_estudo.py` e rode de novo. Leia a mensagem de falha com calma. Ela mostra a linha do
`assert` e a diferença entre o esperado e o obtido. Desfaça a troca.

Para rodar todos os testes do v8:

```bash
python -m pytest cmj/v8
```

Rode só os testes da área em que você mexeu. A suíte completa do projeto é grande e tem testes
antigos que falham por outros motivos.

## Parte B: o lado Vue

Crie a pasta `_frontend/v8/tests/estudo/` e, nela, `livros-tabela.spec.js`:

```js
import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ilhas } from '~@/core/ilhas'
import LivrosTabela from '~@/modules/estudo/ilhas/LivrosTabela.vue'

const livros = [
  { id: 1, titulo: 'Dom Casmurro', autor: 'Machado de Assis', lido: true },
  { id: 2, titulo: 'Vidas Secas', autor: 'Graciliano Ramos', lido: false }
]

function montar() {
  return mount(LivrosTabela, { props: { livros }, attachTo: document.body })
}

describe('ilha estudo-livros', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('o registro de ilhas carrega este componente', async () => {
    const modulo = await ilhas['estudo-livros']()
    expect(modulo.default).toBe(LivrosTabela)
  })

  it('desenha uma linha por livro e conta os lidos', () => {
    const wrapper = montar()
    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
    expect(wrapper.find('[aria-live="polite"]').text()).toBe('1 de 2 lidos')
    wrapper.unmount()
  })

  it('a busca filtra pelo título enquanto a pessoa digita', async () => {
    const wrapper = montar()
    await wrapper.find('#estudo-busca').setValue('vidas')
    const linhas = wrapper.findAll('tbody tr')
    expect(linhas).toHaveLength(1)
    expect(linhas[0].text()).toContain('Vidas Secas')
    wrapper.unmount()
  })

  it('marcar um livro atualiza a contagem e não altera as props', async () => {
    const wrapper = montar()
    await wrapper.findAll('tbody input[type="checkbox"]')[1].trigger('change')
    expect(wrapper.find('[aria-live="polite"]').text()).toBe('2 de 2 lidos')
    expect(livros[1].lido).toBe(false)
    wrapper.unmount()
  })

  it('recarregar busca a lista na API', async () => {
    const resposta = { itens: [{ id: 3, titulo: 'A Hora da Estrela', autor: 'Clarice Lispector', lido: false }] }
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(resposta), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })))
    const wrapper = montar()
    await wrapper.findAll('button')[0].trigger('click')
    await flushPromises()
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
    expect(wrapper.text()).toContain('A Hora da Estrela')
    wrapper.unmount()
  })
})
```

Como ler:

- `describe` agrupa os testes de um assunto, e cada `it` é um teste.
- `mount` cria o componente de verdade, com as props que você passar, num navegador simulado. Não
  há Django nem página: o componente é testado sozinho.
- `wrapper.find` e `wrapper.findAll` procuram elementos, com os mesmos seletores do CSS.
- `setValue` digita num campo e `trigger('change')` dispara um evento. O `await` espera o Vue
  redesenhar antes de conferir.
- `expect(valor).toBe(esperado)` é o `assert` do Vitest.
- O quarto teste confere uma decisão do capítulo 04: o componente altera a própria cópia, e não as
  props que recebeu.
- No último teste, `vi.stubGlobal('fetch', ...)` troca o `fetch` do navegador por um de mentira,
  que devolve a resposta que você escolheu. O teste não fala com servidor nenhum. `flushPromises`
  espera os pedidos pendentes terminarem.

Rode só a sua pasta:

```bash
cd _frontend/v8
npx vitest run tests/estudo
```

Devem passar os cinco. Para rodar todos os testes do v8, use `npm run test`.

## Parte C: o lint

Lint é a conferência automática de estilo e de erros comuns no JavaScript. O servidor do Vite já o
roda enquanto você trabalha, e mostra os erros por cima da página. Para rodar à mão, sem alterar
nenhum arquivo:

```bash
cd _frontend/v8
npx eslint src tests
```

Cuidado com `npm run lint`: ele **corrige e altera** os arquivos. Do lado Python, a formatação é
feita com `black` e `isort`, só nos arquivos que você mudou:

```bash
python -m black cmj/v8/services/s_estudo.py
python -m isort --profile black cmj/v8/services/s_estudo.py
```

## O que você não faz

- **Não rode `npm run build`.** Ele gera a pasta `dist/`, que é versionada e vai para produção. O
  build é feito à parte.
- **Não instale nem atualize pacotes npm com o servidor do Vite no ar.**
- **Não faça commit do exercício.**

## Como é uma funcionalidade de verdade

O exercício pulou uma etapa que o projeto exige: a **spec**. Antes do código, escreve-se um
documento em `docs/specs/` com as regras da funcionalidade, cada uma com um identificador. As
dúvidas são resolvidas com o responsável, e só então vêm os testes e o código. Cada teste aponta a
regra que confere, e um comando verifica que toda regra tem teste.

Você não precisa dominar isso agora. Precisa saber que existe, e ler `docs/specs/README.md` antes
da sua primeira funcionalidade real. Para ver uma spec pronta, abra `docs/specs/v8/templates.md`,
que descreve os layouts do capítulo 03, e depois `cmj/v8/tests/test_templates.py`, com os testes
dela.

## Descarte o exercício

```bash
git restore cmj/v8/views.py cmj/v8/urls.py _frontend/v8/src/core/ilhas.js
rm -r cmj/v8/services/s_estudo.py cmj/v8/tests/test_estudo.py \
      _templates/v8/v8/estudo _templates/v8/v8/partials/estudo \
      _frontend/v8/src/modules/estudo _frontend/v8/tests/estudo
```

Depois confira com `git status`: não deve sobrar nenhum arquivo seu.

## O que você aprendeu

- O caminho de um pedido no Django: rota, view, serviço, template.
- A herança de templates, os quatro layouts e os blocks que uma página preenche.
- O que é uma ilha, como o Django entrega dados a ela e como se escreve um componente Vue.
- Como abrir drawers, modals e toasts.
- Como o JavaScript busca dados no servidor, e quando uma tela vira zona SPA.
- Como testar os dois lados.

## Para onde ir agora

1. `docs/frontend/v8.md`: a referência de uso, com tudo o que este tutorial só mencionou.
2. A demonstração, em `/v8/demo/clientes/` e `/v8/demo/spa/`, com o código em
   `cmj/v8/services/s_demo.py`, `_templates/v8/v8/demo/` e `_frontend/v8/src/modules/demo/`. Ela usa
   todos os recursos do v8, e é o melhor exemplo para copiar.
3. `docs/specs/v8/README.md`: o índice das regras do v8.
4. `docs/backend/convencoes.md`: as convenções do lado Django do projeto.
