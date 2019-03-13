<script>
import Container from './Container'
export default {
  name: 'container-fluid',
  template: Container.template,
  style: Container.style,
  extends: {
    ...Container
  }
}
</script>
