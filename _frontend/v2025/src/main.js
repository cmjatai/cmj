import Vue from 'vue'
import App from './App'

/*
ws/time-refresh recebe uma notificacão sempre que um model do Sapl
é alterado. Um JSON é enviado pelo servidor no formato:
{
  action: 'post_save' | 'post_delete',
  id: 9999, // 9999 - pk do model alterado
  app: 'app_name', // de que app é esse id
  model; 'model_name', // de que model é esse id
}
*/

const app = new Vue({ // eslint-disable-line
  el: '#app',
  components: { App },
  template: '<App/>'
})
