# 02. Primeira página

Neste capítulo você faz uma página inteira só com Django: a lista de livros, com um filtro por
autor. Nada de Vue ainda. São quatro peças, na ordem em que os dados andam: serviço, view, rota e
template.

## 1. O serviço: de onde vêm os dados

Crie o arquivo `cmj/v8/services/s_estudo.py`:

```python
"""Dados do exemplo do tutorial: uma estante fictícia, fixa e na memória."""

LIVROS = (
    {"id": 1, "titulo": "Dom Casmurro", "autor": "Machado de Assis", "lido": True},
    {"id": 2, "titulo": "Vidas Secas", "autor": "Graciliano Ramos", "lido": False},
    {"id": 3, "titulo": "A Hora da Estrela", "autor": "Clarice Lispector", "lido": False},
)


def listar(autor=""):
    """Livros cujo autor contém o texto informado. Sem texto, todos."""
    termo = autor.strip().casefold()
    return [dict(livro) for livro in LIVROS if termo in livro["autor"].casefold()]


def obter(pk):
    """O livro com esse ``id``, ou ``None``."""
    for livro in LIVROS:
        if livro["id"] == pk:
            return dict(livro)
    return None
```

É Python comum, sem nada de Django. Repare em duas coisas:

- O serviço não sabe o que é uma página nem o que é um pedido do navegador. Ele recebe um texto e
  devolve uma lista. Por isso é fácil de testar e de reaproveitar.
- `dict(livro)` devolve uma cópia. Quem recebe a lista pode alterá-la sem estragar o original.

Numa tela de verdade os dados viriam do banco. O formato do serviço seria o mesmo.

## 2. A view: quem atende o pedido

Abra `cmj/v8/views.py`. No começo do arquivo, acrescente `s_estudo` à linha que importa os serviços:

```python
from cmj.v8.services import s_demo, s_estudo, s_global, s_respostas
```

Depois, logo antes da classe `ZonaV8View`, acrescente:

```python
class EstudoLivrosView(PaginaV8View):
    exige = s_global.AUTENTICADO

    def get(self, request):
        autor = request.GET.get("autor", "")[:100]
        livros = s_estudo.listar(autor)
        return responder_pagina(
            request,
            "v8/estudo/livros.html",
            dados_layout(
                "Livros",
                trilha=[("Início", s_global.URL_BASE), ("Livros", None)],
            ),
            {"autor": autor, "livros": livros},
        )
```

Linha a linha:

- `PaginaV8View` é a classe base das páginas do v8. Ela só aceita pedidos de leitura e já sabe o
  que fazer com quem não tem acesso.
- `exige` diz quem pode ver a página. `s_global.AUTENTICADO` é qualquer pessoa com login. Outros
  valores: `None` (todo mundo), `s_global.SUPERUSUARIO` ou o nome de uma permissão do Django.
  **Quem protege a página é a view**, nunca o menu nem o JavaScript.
- `get` atende o pedido. `request.GET` tem o que veio depois do `?` no endereço. O `[:100]` limita o
  tamanho do texto: nunca confie no tamanho do que o usuário manda.
- `responder_pagina` monta a resposta. Ela recebe o pedido, o nome do template, os dados do layout
  e o contexto, que são os dados da sua página.
- `dados_layout` informa o que a moldura precisa: o título, que vai para a aba do navegador, e a
  trilha, que é a linha "Início / Livros" no alto da página. O último item da trilha não tem
  endereço, porque é a página atual.

## 3. A rota: qual endereço chama a view

Abra `cmj/v8/urls.py` e acrescente a rota em `urlpatterns_paginas`, depois da rota do início:

```python
urlpatterns_paginas = [
    re_path(r"^v8/$", views.InicioView.as_view(), name="inicio"),
    re_path(
        r"^v8/estudo/livros/$",
        views.EstudoLivrosView.as_view(),
        name="estudo_livros",
    ),
]
```

- O primeiro argumento é uma expressão regular. `^` marca o começo do caminho e `$` o fim.
- Todo endereço do v8 começa com `v8/` e, sendo página, termina com `/`. A barra final importa:
  neste projeto `/v8/estudo/livros` (sem a barra) é outro endereço, e responde "não encontrado".
- `name` é o apelido da rota. Com ele você escreve links sem repetir o endereço.

## 4. O template: o HTML com lacunas

Crie a pasta `_templates/v8/v8/estudo/` e, dentro dela, o arquivo `livros.html`:

```django
{% extends "v8/layouts/app_sidebar.html" %}
{% block content %}
  <h1 class="v8-pagina-titulo">Livros</h1>

  <form method="get" action="{% url 'cmj.v8:estudo_livros' %}" class="v8-barra-acoes">
    <label class="v8-rotulo" for="filtro-autor">Autor</label>
    <input class="v8-entrada" type="search" id="filtro-autor" name="autor" value="{{ autor }}" maxlength="100">
    <button type="submit" class="v8-btn v8-btn-primario">Filtrar</button>
  </form>

  <table class="v8-tabela">
    <thead>
      <tr>
        <th scope="col">Título</th>
        <th scope="col">Autor</th>
        <th scope="col">Lido</th>
      </tr>
    </thead>
    <tbody>
      {% for livro in livros %}
        <tr>
          <td>{{ livro.titulo }}</td>
          <td>{{ livro.autor }}</td>
          <td>{% if livro.lido %}Sim{% else %}Não{% endif %}</td>
        </tr>
      {% empty %}
        <tr><td colspan="3">Nenhum livro desse autor.</td></tr>
      {% endfor %}
    </tbody>
  </table>
{% endblock %}
```

A linguagem de templates do Django tem dois tipos de marcação:

- `{{ ... }}` escreve um valor. `{{ livro.titulo }}` escreve o título. O Django troca sozinho os
  caracteres perigosos, como `<` e `"`, de modo que um texto vindo do usuário nunca vira HTML.
- `{% ... %}` é um comando: `for`, `if`, `url`, `extends`, `block`.

O que cada comando faz aqui:

- `{% extends "v8/layouts/app_sidebar.html" %}` diz que esta página usa a moldura com barra lateral.
  Tem que ser a primeira linha. O próximo capítulo explica isso em detalhe.
- `{% block content %}...{% endblock %}` é o seu conteúdo. Tudo o que estiver fora de um block é
  ignorado quando o template estende outro.
- `{% url 'cmj.v8:estudo_livros' %}` escreve o endereço da rota a partir do apelido dela. `cmj.v8`
  é o nome do app.
- `{% for %}...{% empty %}...{% endfor %}` repete a linha para cada livro. O trecho depois de
  `{% empty %}` aparece quando a lista está vazia.

As classes `v8-*` (`v8-tabela`, `v8-btn`, `v8-entrada`) são os estilos prontos do v8. A lista
completa está na seção "CSS" de `docs/frontend/v8.md`.

## Veja funcionando

Abra `http://localhost:9098/v8/estudo/livros/`. Se você não estiver logado, o sistema leva à tela de
login e depois volta para a página. Você deve ver:

- a moldura do v8, com o cabeçalho e a barra lateral;
- a trilha "Início / Livros";
- os três livros na tabela.

Digite `clarice` no campo e clique em "Filtrar". O endereço vira
`/v8/estudo/livros/?autor=clarice` e a tabela mostra um livro só. Foi um pedido novo ao servidor: o
navegador enviou o formulário, o Django montou outra página e a devolveu. Não houve JavaScript.

Agora use Ctrl+U para ver o código-fonte. A tabela está lá, pronta. É isso que significa "o Django
desenha a página".

## O que você acabou de fazer

```text
navegador  →  rota (urls.py)  →  view (views.py)  →  serviço (s_estudo.py)
                                       ↓
navegador  ←  HTML pronto  ←  template (livros.html) preenchido com o contexto
```

## Se não funcionou

- **"Página não encontrada"**: confira a barra no fim do endereço e se a rota está dentro de
  `urlpatterns_paginas`.
- **`TemplateDoesNotExist`**: o caminho na view é `v8/estudo/livros.html`, e o arquivo fica em
  `_templates/v8/v8/estudo/livros.html`. São dois `v8` no caminho do arquivo.
- **`NameError: s_estudo`**: faltou acrescentar `s_estudo` na linha de import.
- **Erro de sintaxe no template**: todo `{% for %}` precisa de `{% endfor %}`, todo `{% if %}` de
  `{% endif %}` e todo `{% block %}` de `{% endblock %}`.
- **A página não mudou depois de editar**: o servidor do Django recarrega sozinho quando um arquivo
  Python muda. Olhe o terminal dele: um erro de Python aparece ali.

## Para praticar

1. Acrescente um quarto livro em `s_estudo.py` e recarregue a página.
2. Mostre acima da tabela quantos livros foram encontrados. Dica: `{{ livros|length }}`.
3. Troque `exige` para `None`, saia do sistema e abra a página. Depois volte para
   `s_global.AUTENTICADO`: o exercício precisa dele assim.

Próximo: [03. Layouts e blocks](./03-layouts-e-blocks.md).
