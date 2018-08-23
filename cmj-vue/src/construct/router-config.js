
import DocumentoEdit from './apps/sigad/components/DocumentoEdit'

export const routes = [
  {
      name: 'documento_construct',
      path: '/documento/:id/construct',
      component: DocumentoEdit,
  },
  {
      name: 'documento_construct_create',
      path: '/classe/:id/documento/construct',
      component: DocumentoEdit,
  }
];
