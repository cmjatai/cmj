<template lang="html">
  <transition name="modal">
    <div class="modal-mask"  @click.self="$emit('close')">

          <div class="modal-area modal-header-container">
            <slot name="header">
              default header
            </slot>
          </div>
          <div class="modal-header-actions">
            <slot name="header-actions">
              default header actions
              <button class="modal-default-button" @click="$emit('close')">
                OK
              </button>
            </slot>
          </div>

          <div class="modal-body-container">
            <slot name="body">
              default body
            </slot>
          </div>

          <div class="modal-area modal-footer-container">
            <slot name="footer">
              default footer
            </slot>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'modal',
}
</script>

<style lang="scss">
.modal-mask {
  position: fixed;
  z-index: 9998;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, .95);
  transition: opacity .3s ease;
  display: grid;
  grid-template-rows: 60px 75% auto;
  grid-template-columns: auto 30%;
  grid-template-areas:
    "header headeractions"
    "body body"
    "footer footer";
  justify-items: center;
  align-items: center;
}
.modal-area {
  position: relative;
  width: 100%;
  height: 100%;
  color: white;
}
.modal-header-container {
  grid-area: header;
}
.modal-header-actions {
  grid-area: headeractions;
  color: white;
  justify-self: end;
}
.modal-body-container {
  grid-area: body;
  img {
    max-height: 100%;
    max-width: 100%;
  }
}
.modal-footer-container {
  grid-area: footer;
}
</style>
