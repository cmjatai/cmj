# 01. Visão geral

Antes de escrever código, vale entender quem faz o quê. O v8 junta três ferramentas, e cada uma
tem um papel bem separado.

## Django: o servidor que monta a página

Django é um framework web em Python. Quando o navegador pede um endereço, é o Django que responde.
O caminho de um pedido tem sempre as mesmas etapas:

1. **Rota**: uma lista diz qual código atende cada endereço. No v8 ela fica em `cmj/v8/urls.py`.
2. **View**: a função ou classe Python que atende o pedido. Ela confere quem está pedindo, busca
   os dados e escolhe o template. No v8 fica em `cmj/v8/views.py`.
3. **Serviço**: o código que conhece os dados e as regras. A view não decide regra: ela chama o
   serviço. Esta divisão é uma convenção do projeto, e os serviços ficam em `cmj/v8/services/`.
4. **Template**: um arquivo HTML com lacunas. O Django preenche as lacunas com os dados que a view
   entregou (o **contexto**) e devolve HTML pronto. Os templates do v8 ficam em `_templates/v8/`.

O resultado é uma página HTML completa, que funciona mesmo com o JavaScript desligado.

## Vue: o JavaScript que dá vida a um trecho da tela

Vue é uma biblioteca JavaScript para construir interfaces. Em vez de você procurar elementos na
página e alterá-los à mão, como se faz com `document.querySelector`, no Vue você descreve como a
tela deve ficar para cada estado dos dados, e ele cuida de atualizar o HTML.

A unidade do Vue é o **componente**: um arquivo `.vue` com um pedaço de HTML (o `<template>`) e o
JavaScript que o controla (o `<script setup>`). Quatro ideias bastam para começar:

- **Estado reativo**: um valor guardado com `ref(...)`. Quando ele muda, a tela muda sozinha.
- **Valor calculado**: um valor criado com `computed(...)` a partir de outros. Ele se recalcula
  quando o que ele usa muda.
- **Props**: os dados que o componente recebe de fora, como os parâmetros de uma função.
- **Diretivas**: atributos especiais no `<template>`, como `v-for` (repetir), `v-if` (mostrar ou
  não), `v-model` (ligar um campo a um estado) e `@click` (reagir a um clique).

## Vite: a ferramenta que entrega o JavaScript ao navegador

Num site simples você escreve `<script src="arquivo.js">` e pronto. Com Vue isso não basta: o
navegador não entende arquivos `.vue`, e um projeto tem centenas de arquivos que importam uns aos
outros. O Vite resolve as duas coisas:

- **Durante o desenvolvimento**, ele é um servidor (na porta 5174, no v8) que traduz cada arquivo
  na hora em que o navegador pede. Quando você salva um componente, a tela se atualiza sozinha.
- **Para produção**, ele junta e compacta tudo em poucos arquivos, na pasta `dist/`. Esse passo se
  chama build. **Você não roda o build**: ele é feito à parte, por quem cuida da publicação.

Você quase não mexe no Vite. Basta saber que ele precisa estar no ar para o JavaScript chegar.

## Como o v8 junta os três

Muitos projetos escolhem um extremo: ou o servidor monta tudo e o JavaScript é detalhe, ou o
JavaScript monta tudo e o servidor só entrega dados. O v8 é **híbrido**:

- o Django é dono dos endereços e desenha tudo o que consegue;
- o Vue entra só no trecho da tela que precisa reagir ao usuário sem recarregar.

Isso dá três formas de fazer uma tela, da mais simples para a mais elaborada:

| Forma | Quem desenha | Quando usar |
| --- | --- | --- |
| Página Django | Só o Django | Listagem, detalhe, formulário comum. É o ponto de partida |
| Página Django com ilha | O Django desenha a página, e o Vue assume um trecho dela | Um pedaço da tela precisa de interação: seleção, busca instantânea, gráfico |
| Zona SPA | O Django entrega a moldura, e o Vue desenha todo o miolo | A tela é um pequeno aplicativo, com várias telas internas |

A regra prática: comece pela página Django. Acrescente uma ilha quando um trecho pedir. Zona SPA é
exceção.

## O que acontece quando você abre uma página do v8

1. O navegador pede, por exemplo, `/v8/estudo/livros/`.
2. O Django acha a rota, executa a view e devolve o HTML já com a lista de livros.
3. O navegador mostra a página. Neste momento ela já é legível e os links funcionam.
4. O HTML traz uma referência ao JavaScript do v8, que o navegador busca no Vite.
5. O JavaScript inicia **um único** aplicativo Vue para a página inteira.
6. Esse aplicativo procura na página os trechos marcados como ilha e coloca um componente em
   cada um. Ele também liga os botões de tema e de menu, e passa a atender os links que abrem
   drawers e modals.

Repare na ordem: primeiro existe uma página que funciona, depois o JavaScript a melhora. Se o
JavaScript falhar, o usuário continua com a página do passo 3.

## Onde fica cada coisa

| Caminho | O que tem |
| --- | --- |
| `cmj/v8/urls.py` | As rotas. Todas começam com `/v8/` |
| `cmj/v8/views.py` | As views |
| `cmj/v8/services/` | Os serviços: dados e regras |
| `cmj/v8/templatetags/v8_tags.py` | Comandos extras que os templates do v8 podem usar |
| `cmj/v8/tests/` | Os testes do lado Django |
| `_templates/v8/base_v8.html` | O esqueleto de toda página do v8 |
| `_templates/v8/v8/layouts/` | Os layouts: as molduras prontas |
| `_templates/v8/v8/` | As páginas, organizadas por assunto |
| `_frontend/v8/src/` | Todo o JavaScript, os componentes Vue e o CSS |
| `_frontend/v8/src/modules/<assunto>/` | Os componentes de cada assunto |
| `_frontend/v8/tests/` | Os testes do lado Vue |

## Vocabulário

Estes nomes aparecem no código e nos próximos capítulos.

| Termo | Significado |
| --- | --- |
| Layout | Template que define a moldura da página: cabeçalho, menu, área de conteúdo, rodapé |
| Block | Uma lacuna com nome dentro de um template, que outro template pode preencher |
| Shell | A moldura em si: cabeçalho, menu e trilha de navegação |
| Ilha | Um trecho da página do Django controlado por um componente Vue |
| Zona SPA | Um conjunto de endereços em que o Vue desenha todo o miolo da página |
| Fragmento | Um pedaço de HTML que o Django devolve sozinho, sem a página em volta |
| Drawer | Um painel que desliza de um lado da tela, por cima ou ao lado do conteúdo |
| Modal | Uma janela no centro da tela, que pede atenção antes de continuar |
| Toast | Um aviso curto que aparece num canto e some sozinho |
| Props | Os dados que um componente Vue recebe de fora |

## Duas ferramentas do navegador que você vai usar

- **Ver código-fonte** (Ctrl+U): mostra o HTML exatamente como o Django o enviou. É o que existe
  antes de qualquer JavaScript.
- **Inspecionar** (F12): mostra a página como ela está agora, depois do que o JavaScript fez. A aba
  Console mostra os erros de JavaScript, e a aba Rede mostra cada pedido ao servidor.

Comparar as duas é a melhor forma de entender o que veio do Django e o que veio do Vue.

Próximo: [02. Primeira página](./02-primeira-pagina.md).
