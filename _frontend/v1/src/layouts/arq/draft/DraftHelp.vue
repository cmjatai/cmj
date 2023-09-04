<template>
  <div>
    <hr>
    <h3>O que é o Draft?</h3>
    Draft é uma ferramenta para criação e edição de arquivos PDF/A-2b.<br>
    Esta área é só sua. Os Draft's criados aqui não são públicos e não são vistos por outros usuários.<br>
    Cada Draft é uma área de criação independente, clique no botão "+" acima para incluir um novo Draft.<br>
    <br>
    Em um Draft você pode incluir vários PDFs e até mesmo imagens, bem como desmembrar, excluir, rotacionar e reunir páginas.<br>
    No Draft é possível adicionar vários PDFs e acionar o botão "PDF -> PDF/A-2b" que acionará uma tarefa interna do Draft que transformará seus arquivos em PDF/A-2b com OCR.
    Com seus arquivos já editados, você poderá baixá-los em um arquivo compactado se em seu Draft, possuir mais que um arquivo, ou ainda, clicar sobre ele e abrir uma nova janela para então salvar em seus documentos locais.<br>
    <br>
    Nas próximas versões da ferramenta, em breve, será adicionado reposicionamento de páginas e baixa/alta compactação de imagens para geração de PDFs reduzidos.<br>
    <br>
    No canto superior esquerdo de cada arquivo aparece um círculo que pode possuir três cores:
    <ul>
      <li>Circulo vermelho - Significa que o arquivo não foi analisade desde a adição ou devido a uma edição e não há garantia que possua OCR ou seja um PDF/A-2b</li>
      <li>Circulo amarelo - Significa que você acionou um conversor "PDF -> PDF/A-2b"
          e que o Draft está trabalhando nessa tarefa.
          Tal tarefa não é feita em seu computador e neste momento está sendo feita em nuvem,
          o que significa que você pode fechar o site, ir fazer outras tarefas e,
          mais tarde pegar seus arquivos já convertidos.
          Isso mesmo, se for muitos arquivos e/ou muitos páginas,
          o processo de conversão pode demorar de minutos a horas.
      </li>
      <li>Circulo verde - O processamento de "PDF -> PDF/A-2b" já está concluído e você pode baixar seu arquivo.</li>
    </ul>
    <strong>
      E, muito importante, seu Draft será automaticamente apagado depois de uma semana que você criá-lo, afinal, é um <em>Draft</em>.
    </strong>
  </div>
</template>
<script>
export default {
  name: 'draft-help'
}
</script>
