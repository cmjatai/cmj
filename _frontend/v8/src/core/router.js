import { createRouter, createWebHistory, START_LOCATION } from 'vue-router'
import navegacao from '~@/core/navegacao'
import { zonas } from '~@/core/zonas'
import { instalarSincroniaDePaineis } from '~@/overlays/urlSync'

// Router único do v8 (V8-ARQ-037 a 039).
//
// O Django é o dono das rotas. Aqui só existem as rotas da zona SPA da página atual, se houver,
// e uma rota genérica que representa "a página que o Django entregou". Ir para um caminho fora
// da zona é sempre uma carga normal de página.

const ROTA_DA_PAGINA = 'v8_pagina'
const SemTela = { render: () => null }

// Só os parâmetros que o caminho do registro usa. Passar os demais faria o router reclamar.
export function paramsDoRegistro(registro, params) {
  const usados = [...(registro?.path || '').matchAll(/:([A-Za-z_]\w*)/g)].map(achado => achado[1])
  return Object.fromEntries(usados.filter(nome => nome in params).map(nome => [nome, params[nome]]))
}

export function nomeDaRotaDaZona(zona) {
  return `v8_zona_${zona}`
}

// opcoes: { historico, registroDeZonas, registroDePaineis } servem aos testes.
export async function criarRouter(global, opcoes = {}) {
  const router = createRouter({
    history: opcoes.historico || createWebHistory(),
    routes: [{ path: '/:caminho(.*)*', name: ROTA_DA_PAGINA, component: SemTela }]
  })

  const registro = opcoes.registroDeZonas || zonas
  const prefixo = global.prefixoZona
  const nomeDaZona = global.zona ? nomeDaRotaDaZona(global.zona) : null
  // O nome da zona só é resolvido pelo registro; o prefixo vem do Django (V8-ARQ-011 e 064).
  if (prefixo && Object.hasOwn(registro, global.zona)) {
    try {
      const modulo = await registro[global.zona]()
      const zona = modulo.default || modulo
      router.addRoute({
        path: prefixo.replace(/\/+$/, ''),
        name: nomeDaZona,
        component: zona.layout,
        meta: zona.meta || {},
        children: [
          ...zona.rotas,
          {
            path: ':caminho(.*)*',
            name: `${nomeDaZona}_404`,
            component: () => import('~@/views/Error404.vue')
          }
        ]
      })
    } catch (falha) {
      console.error(`Falha ao carregar as rotas da zona ${global.zona}.`, falha)
    }
  }

  router.beforeEach((to, from) => {
    if (from === START_LOCATION || to.path === from.path) {
      return true
    }
    if (nomeDaZona && to.matched.some(registroDaRota => registroDaRota.name === nomeDaZona)) {
      return true
    }
    navegacao.ir(to.fullPath)
    return false
  })

  instalarSincroniaDePaineis(router, { registro: opcoes.registroDePaineis })
  return router
}
