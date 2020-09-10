// { path: '',
//   name: 'index_link',
//   component: () => import('@/pages/Index.vue')
// },

export const routes = [
  {
    path: '',
    component: () => import('@/App.vue'),
    children: [

    ]
  },
  {
    path: '*',
    name: '404',
    component: {
      template: '<p>Page Not Found</p>'
    }
  }
]
