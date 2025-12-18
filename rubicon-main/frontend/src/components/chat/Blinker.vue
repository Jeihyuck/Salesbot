<template>
  <div class="blinker">
    <slot />
  </div>
</template>

<style>
@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

.blinker {
  animation: blink 3s infinite; /* Adjust duration (1s) */
  color:#2fb7e5;
  padding: 0.2em;
  font-size: 1em;
  font-weight: 600;
}
</style>