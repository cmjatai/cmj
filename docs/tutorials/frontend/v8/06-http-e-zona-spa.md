# 06. HTTP e zona SPA

Até aqui todo dado chegou junto com a página. Neste capítulo o componente busca dados no servidor
depois que a página já está aberta. No fim, você conhece a zona SPA, a forma de tela em que o Vue
desenha o miolo inteiro.

## Parte A: buscar dados pelo JavaScript

Vamos acrescentar um botão "Recarregar", que pede a lista de livros ao servidor e redesenha a
tabela, sem recarregar a página.

### 1. Um endereço que devolve JSON

Em `cmj/v8/views.py`, depois de `EstudoLivroFragmento`:

```python
class EstudoApiLivrosView(JsonV8View):
    exige = s_global.AUTENTICADO
    http_method_names = ["get"]

    def get(self, request):
        return JsonResponse({"itens": s_estudo.listar()})
```

Em `cmj/v8/urls.py`, depois da rota do fragmento:

```python
    re_path(
        r"^v8/estudo/api/livros/$",
        views.EstudoApiLivrosView.as_view(),
        name="estudo_api_livros",
    ),
```

- `JsonV8View` é a classe base dos endereços que devolvem dados. Quando o acesso é negado ou o
  registro não existe, ela responde em JSON, e não com uma página de erro.
- `http_method_names = ["get"]` diz que este endereço só aceita leitura.
- `JsonResponse` transforma o dicionário Python em JSON.
- A view chama o **mesmo** serviço que a página. A regra continua num lugar só.

Abra `http://localhost:9098/v8/estudo/api/livros/` no navegador. Aparece o JSON com os três
livros. Um endereço assim é feito para o JavaScript ler, não para uma pessoa.

### 2. O pedido, no componente

Em `LivrosTabela.vue`, na seção de imports:

```js
import http, { HttpError } from '~@/http/client'
```

Na seção de funções:

```js
async function recarregar() {
  try {
    const resposta = await http.get('/v8/estudo/api/livros/')
    lista.value = resposta.itens
    toast.info('Lista recarregada.')
  } catch (erro) {
    toast.error(erro instanceof HttpError ? erro.mensagem : 'Não foi possível recarregar.')
  }
}
```

E no `<template>`, entre o campo de busca e o botão "Desmarcar todos":

```vue
      <button
        type="button"
        class="v8-btn"
        @click="recarregar"
      >
        Recarregar
      </button>
```

Teste: marque todos os livros e clique em "Recarregar". A lista volta ao que o servidor tem, e a
contagem acompanha. Na aba Rede (F12) aparece o pedido a `/v8/estudo/api/livros/`.

### O que há de novo

- `http.get(...)` devolve uma Promise, como o `confirm` do capítulo anterior. O `await` espera a
  resposta, já convertida de JSON para um objeto JavaScript.
- `lista.value = resposta.itens` troca a lista inteira. A tabela e a contagem se redesenham sem você
  pedir, porque dependem de `lista`.
- `try` e `catch`: se o pedido falhar, a execução pula para o `catch`. O erro é sempre um
  `HttpError`, com uma mensagem pronta em `erro.mensagem` e um código em `erro.codigo`, como
  `sem_permissao`, `nao_encontrado`, `validacao`, `servidor` ou `rede`.

Para ver o erro acontecer, pare o servidor do Django e clique em "Recarregar". Aparece o toast de
erro. Suba o servidor de novo.

### Por que `http`, e não `fetch`

O navegador já tem a função `fetch` para pedidos. No v8 você **nunca** a chama direto: usa o
cliente `http`, de `~@/http/client`. Ele faz o que todo pedido precisa e que é fácil esquecer:

- envia o token de segurança (CSRF) que o Django exige em todo pedido que grava;
- recusa endereço de outro site;
- entrega qualquer falha no mesmo formato, o `HttpError`;
- quando a sessão expira no meio do uso, pede novo login e refaz o pedido.

Além de `get`, existem `post`, `put`, `patch` e `delete`. Os que enviam dados recebem um objeto
como segundo argumento: `await http.post(url, { titulo: 'Novo livro' })`.

### E gravar?

O exercício não grava nada, porque não tem banco. O caminho de uma gravação de verdade seria:

1. o componente chama `http.post` ou `http.put` com os dados;
2. a view confere o acesso e valida os dados com um formulário do Django;
3. se os dados são inválidos, ela responde com o status 400 e os erros de cada campo;
4. o componente mostra cada erro junto ao campo.

A demonstração faz tudo isso. Veja `DemoApiClientesView` em `cmj/v8/views.py`, do lado Django, e
`_frontend/v8/src/modules/demo/modais/ClienteForm.vue`, do lado Vue.

## Parte B: zona SPA

SPA quer dizer "aplicativo de página única": a pessoa navega entre várias telas e o navegador nunca
carrega uma página nova. Quem troca as telas é o JavaScript.

Numa **zona SPA** do v8:

- o Django entrega a moldura (cabeçalho, menu, trilha) e um espaço vazio no conteúdo;
- o Vue desenha tudo o que vai nesse espaço e cuida dos endereços internos da zona;
- os dados chegam sempre pelo cliente `http`.

A zona tem um prefixo, como `/v8/demo/spa`. Qualquer endereço que comece com ele recebe a mesma
página do Django, e o Vue decide o que mostrar a partir do resto do endereço.

### Quando usar

Zona SPA custa mais: nada funciona sem JavaScript, a tela demora mais para mostrar conteúdo, e
tudo o que o Django faria de graça (listar, paginar, validar) precisa de um endereço de dados e de
código Vue. Ela compensa quando a tela é de fato um aplicativo: muitas telas internas ligadas
entre si, estado que não pode se perder a cada clique, edição intensa.

Na dúvida, não é zona. Comece pela página com ilhas.

| Pergunta | Se sim |
| --- | --- |
| O Django consegue desenhar a tela, e o usuário só lê e segue links? | Página Django |
| Um trecho precisa reagir na hora, sem recarregar? | Página Django com ilha |
| Há várias telas internas que trocam sem recarregar, com estado comum? | Zona SPA |

### Um passeio pela zona da demonstração

Você não vai construir uma zona neste tutorial. Em vez disso, leia a que existe, nesta ordem. Abra
`/v8/demo/spa/` em outra aba para acompanhar (exige superusuário).

1. **`cmj/v8/services/s_global.py`, o dicionário `ZONAS`.** Cada zona é declarada uma vez, com
   nome, prefixo, título, quem pode acessar e o layout. As rotas do Django saem dessa lista.
2. **`_templates/v8/v8/paginas/zona.html`.** A página de toda zona. Repare que ela só tem um
   elemento com o atributo `data-vue-zone` e um texto de espera. É o "espaço vazio".
3. **`_frontend/v8/src/core/zonas.js`.** O registro: qual módulo atende cada zona. É o mesmo
   princípio do registro de ilhas.
4. **`_frontend/v8/src/modules/demo/zona.js`.** As rotas internas da zona. Cada uma liga um caminho
   a um componente. Os caminhos são relativos ao prefixo: `clientes` quer dizer
   `/v8/demo/spa/clientes`.
5. **`_frontend/v8/src/modules/demo/spa/DemoSpaLayout.vue`.** O componente que envolve todas as
   telas da zona. O `<RouterView />` dentro dele é o lugar em que a tela da rota atual aparece.
6. **`_frontend/v8/src/modules/demo/spa/ClientesLista.vue`.** Uma tela inteira em Vue: busca os
   dados pelas funções de `modules/demo/api.js`, que usam o cliente `http`, mostra o estado de
   carga, trata erro e desenha a tabela.

Enquanto lê, navegue pela zona com a aba Rede aberta. Ao clicar num cliente, o endereço muda e
aparece um pedido de dados, e nenhum pedido de página.

Dentro de uma zona, os links para as telas dela usam o componente `<RouterLink>`. Um link para
fora da zona é um `<a href>` comum, e carrega uma página nova.

## Se não funcionou

- **O botão não faz nada e o Console mostra `http is not defined`**: faltou o import.
- **Aparece um aviso de sessão expirada ou de falta de permissão**: o endereço de dados também tem
  `exige`. Confira o seu login.
- **Toast "Não encontrado."**: o endereço no componente e a rota no Django estão diferentes.
  Compare letra a letra, inclusive a barra final.

## Para praticar

1. Faça o botão "Recarregar" ficar desabilitado enquanto o pedido está em andamento. Dica: um
   `ref(false)` chamado `carregando`, ligado antes do `await` e desligado num bloco `finally`.
2. Acrescente ao endereço de dados o filtro por autor, lendo `request.GET` como a página faz, e
   teste no navegador com `?autor=clarice`.
3. Na zona da demonstração, descubra em `zona.js` como o detalhe do cliente abre num drawer.

Próximo: [07. Testes](./07-testes.md).
