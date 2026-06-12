<template>
  <div id="app-root">
    <router-view />
  </div>
</template>

<script setup lang="ts">
</script>

<style>
* { margin:0; padding:0; box-sizing:border-box; }

body {
  font-family:'Inter','SF Pro Display',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:#f8fafc; color:#1e293b; -webkit-font-smoothing:antialiased;
}

#app-root { min-height:100vh; }

/* 滚动条 */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:#cbd5e1; border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#94a3b8; }

/* PrimeVue 覆盖：统一品牌色 */
:root {
  --p-primary-color:#6366f1;
  --p-primary-hover-color:#4f46e5;
  --p-primary-active-color:#4338ca;
  --p-button-primary-background:linear-gradient(135deg,#6366f1,#3b82f6);
  --p-button-primary-hover-background:linear-gradient(135deg,#4f46e5,#2563eb);
  --p-button-primary-border-color:transparent;
  --p-button-border-radius:8px;
  --p-inputtext-border-color:#e2e8f0;
  --p-inputtext-focus-border-color:#6366f1;
}
</style>
