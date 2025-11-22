<script lang="ts">
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher();

  let waferId = "";
  let lotId = "";
  let message = "";

  function submit() {
    dispatch("submit", { waferId, lotId, message });
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Enter") {
      submit();
    }
  }
</script>

<header class="top-bar">
  <div class="logo">
    WAFER ANALYZER
  </div>

  <div class="controls">
    <label class="field">
      <span class="field-label">Wafer ID</span>
      <input
        class="field-input"
        placeholder="예: 24"
        bind:value={waferId}
        on:keydown={handleKeydown}
      />
    </label>

    <label class="field">
      <span class="field-label">Lot</span>
      <input
        class="field-input"
        placeholder="예: 4175341"
        bind:value={lotId}
        on:keydown={handleKeydown}
      />
    </label>

    <label class="field field-wide">
      <span class="field-label">옵션</span>
      <input
        class="field-input"
        placeholder="필터, 그룹 등 메모"
        bind:value={message}
        on:keydown={handleKeydown}
      />
    </label>

    <button class="btn-generate" type="button" on:click={submit}>
      Generate
    </button>
  </div>
</header>

<style>
  .top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 10px 20px;
    border-bottom: 1px solid #e5e7eb;
    background: #f9fafb;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
      sans-serif;
  }

  .logo {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    background: linear-gradient(90deg, #6366f1, #a855f7);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    white-space: nowrap;
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    justify-content: flex-end;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 130px;
  }

  .field-wide {
    min-width: 240px;
    flex: 1;
  }

  .field-label {
    font-size: 10px;
    text-transform: uppercase;
    color: #6b7280;
    letter-spacing: 0.08em;
  }

  .field-input {
    height: 30px;
    padding: 4px 8px;
    font-size: 13px;
    border-radius: 6px;
    border: 1px solid #d1d5db;
    background: #f9fafb;
    color: #111827;
    outline: none;
  }

  .field-input:focus {
    border-color: #6366f1;
    box-shadow: 0 0 0 1px #6366f1;
    background: #ffffff;
  }

  .btn-generate {
    height: 32px;
    padding: 0 18px;
    border-radius: 999px;
    border: none;
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    color: white;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }

  .btn-generate:hover {
    filter: brightness(1.05);
  }

  .btn-generate:active {
    filter: brightness(0.95);
  }

  /* 화면이 좁을 때는 인풋이 밑으로 내려가도록 */
  @media (max-width: 900px) {
    .top-bar {
      flex-direction: column;
      align-items: flex-start;
    }

    .controls {
      width: 100%;
      flex-wrap: wrap;
      justify-content: flex-start;
    }

    .field,
    .field-wide {
      flex: 1 1 140px;
    }
  }
</style>
