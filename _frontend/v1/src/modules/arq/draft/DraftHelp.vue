<template>
  <div>
    <hr>
    <h3>O que é o Draft?</h3>
    <h5 style="padding-left: 5vw; padding-bottom: 1em;">
      Draft é uma ferramenta para criação e edição de arquivos PDF/A-2b,<br>além de também fazer OCR e converter DOC, DOCx, ODT, XLS, XLSX, ODS, TIF, TIFF, PNG e JPG para PDFs.<br>
    </h5>
    Esta área é só sua. Os Drafts criados aqui não são públicos e não são vistos por outros usuários.<br>
    Cada Draft é uma área de criação independente. Clique no botão "+" acima para incluir um novo Draft.<br>
    <br>
    Em um Draft você pode incluir vários PDFs, bem como desmembrar, excluir, rotacionar e reunir páginas. <br>
    Alem de arquivos DOC, DOCx, ODT, XLS, XLSX, ODS, PNG e JPG, que serão imediatamente convertidos para PDF.<br>
    <br>
    No Draft é possível adicionar vários PDFs e clicar no botão "PDF -> PDF/A-2b" que acionará uma tarefa interna do Draft que transformará seus arquivos em PDF/A-2b com OCR.
    Com seus arquivos já editados, você poderá baixá-los em um arquivo compactado se em seu Draft houver mais que um arquivo ou ainda clicar sobre ele e abrir uma nova janela para então salvar em seus documentos locais.<br>
    <div class="d-none">
      Nas próximas versões da ferramenta, em breve, será adicionado reposicionamento de páginas e baixa/alta compactação de imagens para geração de PDFs reduzidos.<br>
    </div>
    No canto superior esquerdo de cada arquivo aparece um círculo que pode possuir três cores:
    <ul>
      <li>Círculo vermelho - Significa que o arquivo não foi analisado desde a adição ou devido a edições, e não há garantia que possua OCR ou seja um PDF/A-2b.</li>
      <li>Circulo amarelo - Significa que você acionou um conversor "PDF -> PDF/A-2b" e que o Draft está trabalhando nessa tarefa.
        Tal tarefa não é feita em seu computador e neste momento está sendo feita em nuvem, o que significa que você pode fechar o site,
        ir fazer outras tarefas e, mais tarde, pegar seus arquivos já convertidos.
        Isso mesmo: se forem muitos arquivos e/ou muitas páginas, o processo de conversão pode demorar de minutos a horas.
      </li>
      <li>Circulo verde - O processamento de "PDF -> PDF/A-2b" já está concluído e você pode baixar seu arquivo.</li>
    </ul>
    Já no canto superior direito, em "<small><i class="fas fa-ellipsis-v"></i></small>", você encontra as opções exclusivas do PDF em edição,
    que seria:
    <ul>
      <li>"PDF -> PDF/A-2b" - do PDF em específico.</li>
      <li>"Decompor" - que decompõe um PDF de várias páginas em vários PDFs de uma página.</li>
      <li>"Excluir" - que exclui apenas o PDF em edição.</li>
    </ul>
    <strong>
      E, muito importante, seu Draft será automaticamente apagado depois de uma semana que você o criar, afinal, é um <em>Draft</em> ("rascunho", em inglês).
    </strong>
  </div>
</template>
<script>
export default {
  name: 'draft-help'
}
</script>
