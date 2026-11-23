// Registro de ilhas (V8-ARQ-033): o nome usado em data-vue-island e quem o carrega.
// Só o que está aqui pode ser montado (V8-ARQ-064).
export const ilhas = {
  'demo-clientes-tabela': () => import('~@/modules/demo/ilhas/ClientesTabela.vue'),
  'ds-overlays': () => import('~@/modules/ds/ilhas/DsOverlays.vue'),
  'ds-componentes': () => import('~@/modules/ds/ilhas/DsComponentes.vue'),
  'ds-campos': () => import('~@/modules/ds/ilhas/DsCampos.vue'),
  'ds-estrutura': () => import('~@/modules/ds/ilhas/DsEstrutura.vue'),
  'ds-datas': () => import('~@/modules/ds/ilhas/DsDatas.vue'),
  'ds-cor': () => import('~@/modules/ds/ilhas/DsCor.vue')
}
