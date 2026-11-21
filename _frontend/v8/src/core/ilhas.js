// Registro de ilhas (V8-ARQ-033): o nome usado em data-vue-island e quem o carrega.
// Só o que está aqui pode ser montado (V8-ARQ-064).
export const ilhas = {
  'demo-clientes-tabela': () => import('~@/modules/demo/ilhas/ClientesTabela.vue')
}
