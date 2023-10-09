<template>
  <div :class="['base-layout', sideleft_expand ? 'left-expand': '']">

    <header>

      <div class="header-left">
        <slot name="header-left"></slot>
        <a class="nav-toggler" @click="toogle_sideleft">
          <span class="line"></span>
          <span class="line"></span>
          <span class="line"></span>
        </a>
      </div>

      <div class="header-main">
        <div class="brand">
            <slot name="brand"></slot>
        </div>
        <div class="header-detail">
          a<slot name="header-detail"></slot>
        </div>
      </div>

      <div class="header-right">
        <slot name="header-right"></slot>
      </div>
    </header>

    <div class="sideleft">
      <slot name="sideleft"></slot>
    </div>

    <div class="main" v-on:scroll.passive="handleScroll">
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
      sideleft_expand: false,
      count_time: 0,
      id_interval: 0
    }
  },
  methods: {
    toogle_sideleft: function () {
      this.sideleft_expand = !this.sideleft_expand
    },
    handleScroll () {
      // console.log('scroll')
      let t = this
      if (t.count_time === 0) {
        t.count_time += 1
        if (t.id_interval !== 0) {
          clearInterval(t.id_interval)
        }
        t.id_interval = setInterval(() => {
          // console.log(t.count_time)
          t.count_time += 1
        }, 5000)
      } else if (t.count_time > 12) {
        t.count_time = 0
        t.$disconnect()
        t.$connect()
      } else {
        t.count_time = 0
      }
    }
  },
  mounted: function () {
    document.querySelector('body').classList.add('body-base-layout')
  }
}
</script>

<style lang="scss">
@import "~@/scss/variables";

.body-base-layout {
  overflow: hidden;
}

.base-layout {
  user-select: none;
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-color: transparent;

  font-size: 1rem;
  line-height: 1;

  display: grid;
  grid-template-columns: $width-sideleft $width-sideleft * 3 auto $width-sideright;
  grid-template-rows: 60px auto;
  z-index: 4000;

  .btn-outline-dark {
    border: 1px solid #bbb;
    background-image: linear-gradient(to bottom, #fff, #e5e5e5);
    &:hover, &:not(.disabled).active {
      border: 1px solid #888;
      background-image: linear-gradient(to bottom, #e5e5e5, #fff);
      color: black;
    }
  }

  header {
    display: grid;
    grid-template-columns: $width-sideleft auto $width-sideleft;
    grid-row-start: 1;
    grid-row-end: 2;
    grid-column-start: 1;
    grid-column-end: 5;
    align-content: stretch;
    height: 60px;

    background-color: rgba($color: #f5f5f5, $alpha: 1);
    border-bottom: 1px #ddd solid;

    .header-left {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .header-main {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .nav-toggler {
      width: 48px;
      height: 48px;
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
    .btn-outline-dark {
      font-size: 140%;
      line-height: 1.7;
      padding: 0 20px;
    }
  }

  .sideleft, .main, .sideright {
    grid-row-start: 2;
    grid-row-end: 3;
    background-color: rgba($color: #f0f0f0, $alpha: 1);
    background-image: url("~@/assets/img/bg.png");
  }

  .sideleft {
    grid-column-start: 1;
    grid-column-end: 2;
    border-right: 1px #ddd solid;
  }

  .main {
    grid-column-start: 2;
    grid-column-end: 4;
    overflow: auto;
  }

  .sideright {
    grid-column-start: 4;
    grid-column-end: 5;
    border-left: 1px #ddd solid;
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

  .empty-list {
    background-color: rgba($color: #e0e0e0, $alpha: 0.9);
    background-image: url("~@/assets/img/bg.png");
    padding: 3rem;
    text-align: center;
    font-size: 120%;
  }

  .hover-circle:hover {
    background-color: #dddddd;
    border-radius: 50%;
  }

}

@media screen and (max-width: 800px){

  $width-sideleft: 48px;
  $width-sideright: 48px;

  .base-layout {
    grid-template-columns: $width-sideleft $width-sideleft * 3 auto $width-sideright;

    font-size: 0.9rem;
    header {
      grid-template-columns: $width-sideleft auto $width-sideleft;
      .nav-toggler {
        width: 40px;
        height: 40px;
      }
      .btn-outline-dark {
        line-height: 1.7;
        padding: 0 15px;
      }

    }
  }
}

@media screen and (max-width: 600px) {

  .base-layout {
    header {
      .ml-2 {
        margin-left: 0.25rem !important;
      }
      .btn-outline-dark {
        font-size: 90%;
        line-height: 1.7;
        padding: 0 8px;
      }

    }
  }
}

@media screen and (max-width: 480px){

  $width-sideleft: 40px;
  $width-sideright: 36px;

  .base-layout {
    grid-template-columns: $width-sideleft $width-sideleft * 3 auto $width-sideright;

    header {
      grid-template-columns: auto 1px $width-sideleft;
      .header-left {
        display: none;
      }
      .header-main {
        padding-left: 0.5rem;
        flex-direction: column;
        justify-content: center;
        align-items: flex-start;
      }

      .btn-outline-dark {
        margin-top: 2px;
        font-size: 75%;
        line-height: 1.2;
        padding: 0 18px;
      }
    }
  }
}

@media screen and (max-width: 360px) {
  .base-layout {
    font-size: 0.82rem;
  }
}

@media screen and (max-width: 320px) {

  .base-layout {
    font-size: 0.7rem;
  }
}

@media screen and (min-width: 481px) {
  .base-layout:not(.left-expand) {
    //grid-template-columns: 0 0 auto 0px;
  }
}

</style>
