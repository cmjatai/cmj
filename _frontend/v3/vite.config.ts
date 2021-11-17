import vue from '@vitejs/plugin-vue'
import { UserConfig } from 'vite'

const config: UserConfig = {
  plugins: [
    vue(),
  ],
  clearScreen: false
}

export default config
