<template>
  <div class="side-right">
    <div class="menu">
      <ul>
        <li>
          <NormasDestaque />
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import NormasDestaque from '~@/components/NormasDestaque.vue'
</script>
<style lang="scss">
.side-right {
  min-height: calc(100vh - var(--header-height));
  text-align: center;
  
  background-color: var(--cmj-sideright-bg);
  &:hover {
    background-color: var(--cmj-sideright-bg-hover);
  }
  // box-shadow: -10px 0 20px var(--bs-body-bg);

  .menu {
    //border-left: 1px solid var(--bs-border-color-translucent);
    //padding-bottom: 1rem;
    ul {
      list-style-type: none;
      padding: 0;
      margin: 0;
      li {
        margin-bottom: 1em;
        img {
          cursor: pointer;
          width: 2.5em;
        }
        ul {
          position: absolute;
          top: 1em;
          right: 100%;
          height: calc(100vh - 6em);
          z-index: 1;
          white-space: nowrap;
          display: none;
          flex-direction: column;
          justify-content: stretch;
          li {
            flex: 1 1 auto;
            margin: 0;
            padding: 0;
            button {
              height: 100%;
              width: 100%;
              text-align: left;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
              border-radius: 0;
            }
            &:not(:last-child) {
              border-bottom: 1px solid var(--bs-border-color);
            }
          }
        }
        &:hover ul {
          display: flex;
        }
      }
    }
  }
}
</style>
