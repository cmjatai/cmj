// Registro de zonas SPA (V8-ARQ-037): o nome que o Django informa e o módulo de rotas da zona.
// O prefixo de cada zona vem do Django, em #v8-global.
//
// O módulo exporta por padrão { layout, rotas }: o componente que envolve a zona e as rotas
// filhas, com caminhos relativos ao prefixo.
export const zonas = {
  'demo-spa': () => import('~@/modules/demo/zona')
}
