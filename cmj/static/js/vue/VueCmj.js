import Vue from 'vue'
import VueResource from 'vue-resource'
import Exemplo from './components/Exemplo.vue'

Vue.use(VueResource)

new Vue(Exemplo).$mount(".exemplo")
