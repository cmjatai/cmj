
import App from './App.vue'
import { defineAsyncComponent } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

// cmj = PortalCMJ Frontend

const rootComponents = {
  // Para ser utilizado em templates Django se não estiver em globalComponents.
  'cmj-app': App,
  'cmj-error-404': defineAsyncComponent(() => import('~@/views/Error404.vue'))
}

const globalComponents = {
  FontAwesomeIcon,

  // Para ser utilizado em qualquer componente Vue sem necessidade de importação.
  // O colocado em globalComponents não precisa ser colocado em rootComponents.
  'cmj-refresh-page': defineAsyncComponent(() => import('~@/components/atoms/RefreshPage.vue')),
  'cmj-alert': defineAsyncComponent(() => import('~@/components/atoms/Alert.vue')),

  'WidgetHtmlCode': defineAsyncComponent(() => import('~@/modules/painelset/widgets/utils/WidgetHtmlCode.vue')),
  'WidgetYoutubeEmbed': defineAsyncComponent(() => import('~@/modules/painelset/widgets/utils/WidgetYoutubeEmbed.vue')),

  'WidgetSessaoPlenariaStatus': defineAsyncComponent(() => import('~@/modules/painelset/widgets/sessao/WidgetSessaoPlenariaStatus.vue')),
  'WidgetSessaoRegistroPresenca': defineAsyncComponent(() => import('~@/modules/painelset/widgets/sessao/WidgetSessaoRegistroPresenca.vue')),
  'WidgetSessaoItemEmPauta': defineAsyncComponent(() => import('~@/modules/painelset/widgets/sessao/WidgetSessaoItemEmPauta.vue')),

  'WidgetCronometroEvento': defineAsyncComponent(() => import('~@/modules/painelset/widgets/painelset/WidgetCronometroEvento.vue')),
  'WidgetCronometroPalavra': defineAsyncComponent(() => import('~@/modules/painelset/widgets/painelset/WidgetCronometroPalavra.vue')),
  'WidgetStatusEventoSessao': defineAsyncComponent(() => import('~@/modules/painelset/widgets/painelset/WidgetStatusEventoSessao.vue'))

}

export default {
  rootComponents,
  globalComponents
}
