<script lang="ts">
  import "../app.css";     // ★ Tailwind 4.x 로딩
  import favicon from '$lib/assets/favicon.svg';

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

{@render children()}
