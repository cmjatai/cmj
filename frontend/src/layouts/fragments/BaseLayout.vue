<template>
  <div :class="['base-layout', sideleft_expand ? 'left-expand': '']">
    <header>
      <div class="navigation">
        <slot name="navigation"></slot>
        <a class="nav-toggler" @click="toogle_sideleft">
          <span class="line"></span>
          <span class="line"></span>
          <span class="line"></span>
        </a>
      </div>
      <div class="brand">
          <slot name="brand"></slot>
      </div>
      <div class="header-main">
        <slot name="header-main"></slot>
      </div>
      <div class="header-right">
        <slot name="header-right"></slot>
      </div>
    </header>
    <div class="sideleft">
      <slot name="sideleft"></slot>
    </div>
    <div class="main">
      <slot name="main"></slot>
    </div>
    <div class="sideright">
      <slot name="sideright"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'base-layout',
  data () {
    return {
      sideleft_expand: false
    }
  },
  methods: {
    toogle_sideleft: function () {
      this.sideleft_expand = !this.sideleft_expand
    }
  },
  mounted: function () {
    document.querySelector('body').classList.add('body-base-layout')
  }
}
</script>

<style lang="scss">
@import '~bootstrap/scss/bootstrap';

.body-base-layout {
  overflow: hidden;
}

.grid-template-columns {
  grid-template-columns: 64px 186px auto 0px;
}

.row-top {
  grid-row-start: 1;
  grid-row-end: 2;
}

.row-middle {
  grid-row-start: 2;
  grid-row-end: 3;
}

.base-layout {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-color: transparent;
  z-index: $zindex-fixed;
  display: grid;

  @extend .grid-template-columns;
  grid-template-rows: 60px auto;

  header {
    display: grid;
    @extend .row-top;

    grid-template-columns: 64px 2fr 1fr 64px;
    grid-column-start: 1;
    grid-column-end: 5;

    align-content: stretch;

  }

  .sideleft {
    @extend .row-middle;
    grid-column-start: 1;
    grid-column-end: 2;

  }

  .main {
    grid-row-start: 2;
    grid-row-end: 3;
    grid-column-start: 2;
    grid-column-end: 4;
    overflow: auto;
  }

  .sideright {
    @extend .row-middle;
    grid-column-start: 4;
    grid-column-end: 5;
  }

  &.left-expand {
    .sideleft {
      grid-column-start: 1;
      grid-column-end: 3;
    }
    .main {
      grid-column-start: 3;
      grid-column-end: 4;
    }
  }
}

$padding-space: 1rem;

.base-layout {
  .hover-circle:hover {
    background-color: #dddddd;
    border-radius: 50%;
  }
  header, .sideleft {
    background-color: rgba($color: #f5f5f5, $alpha: 1);
  }
  .main, .sideleft, .sideright  {
    background-color: rgba($color: #f0f0f0, $alpha: 1);
    background-image: url("~@/assets/img/bg.png");
  }
  header {
    border-bottom: 1px #ddd solid;
  }
  .sideright {
    // border-left: 1px #ddd solid;
  }
}

.base-layout {
  .main {
    text-align: justify;
    padding: $padding-space;
    padding-bottom: 0;
  }

  header {
    .navigation, .brand, .header-main, .header-right {
      padding: 8px;
      height: 60px;
    }
    .navigation {
      padding: 6px 4px 6px 12px;
    }
  }

  .nav-toggler {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-radius: 50%;
    cursor: pointer;

    .line {
      background: #000;
      display: block;
      height: 2px;
      width: 22px;
      margin: 2px;
    }
    &:hover {
      background-color: #ddd;

    }
  }

  .empty-list {
    background-color: rgba($color: #e0e0e0, $alpha: 0.9);
    background-image: url("~@/assets/img/bg.png");
    padding: 3rem;
    text-align: center;
    font-size: 120%;
  }

}

</style>
