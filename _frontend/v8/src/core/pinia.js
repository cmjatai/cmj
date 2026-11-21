import { createPinia } from 'pinia'

// O único Pinia da página (V8-ARQ-030). Tudo o que precisa de store fora de um componente usa este.
const pinia = createPinia()

export default pinia
