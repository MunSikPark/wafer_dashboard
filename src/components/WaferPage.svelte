<script lang="ts">
  import { onMount } from "svelte";
  import WaferMapPanel from "./WaferMapPanel.svelte";
  import WaferInputBar from "./WaferInputBar.svelte";
  import TrendCorrelationPanel from "./TrendCorrelationPanel.svelte";

  const DATA_URL = "/wafer_bin.json";

  let wafers: any[] = [];
  let currentIndex = 0;
  let loading = true;
  let error = "";
  let generating = false;
  let generateMessage = "";

  // 상관계수 패널용 상태 (나중에 실제 값 채울 예정)
  let corrTargetName = "";
  let correlations: any[] = [];

  $: currentWafer = wafers.length ? wafers[currentIndex] : null;

  onMount(async () => {
    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      wafers = data;
      currentIndex = 0;
    } catch (e) {
      console.error(e);
      error = String(e);
    } finally {
      loading = false;
    }
  });

  function next() {
    if (!wafers.length) return;
    currentIndex = (currentIndex + 1) % wafers.length;
  }

  function prev() {
    if (!wafers.length) return;
    currentIndex = (currentIndex - 1 + wafers.length) % wafers.length;
  }

  // WaferInputBar → submit 이벤트 처리
  async function handleInputSubmit(event: CustomEvent<{ waferIds: string[] }>) {
    const { waferIds } = event.detail;
    console.log("Requested waferIds:", waferIds);

    if (!waferIds.length) {
      generateMessage = "웨이퍼 ID를 하나 이상 입력해주세요.";
      return;
    }

    generating = true;
    generateMessage = "데이터 생성 중...";

    try {
      const res = await fetch("/api/generate-data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ waferIds })
      });

      const json = await res.json();
      if (!res.ok) {
        console.error(json);
        generateMessage = `에러: ${json.error ?? "서버 오류"}`;
        return;
      }

      console.log("generate-data results:", json);
      generateMessage = `데이터 생성 완료: ${json.waferIds.join(", ")}`;
    } catch (e) {
      console.error(e);
      generateMessage = "요청 중 오류가 발생했습니다.";
    } finally {
      generating = false;
    }
  }
</script>

<div class="wafer-page-root">
  <!-- 상단 인풋 바 (한 번만!) -->
  <WaferInputBar on:submit={handleInputSubmit} />

  <!-- 상태 메시지 -->
  {#if generateMessage}
    <div class="status-message">
      {generateMessage}
    </div>
  {/if}

  <!-- 메인 컨텐츠 -->
  <div class="content-area">
    {#if loading}
      <div class="text-muted">Loading wafer data...</div>
    {:else if error}
      <div class="text-error">Error: {error}</div>
    {:else if !currentWafer}
      <div class="text-muted">No wafer data.</div>
    {:else}
      <!-- 제목 -->
      <header class="page-header">
        <div class="page-title">Wafer Map Viewer</div>
      </header>

      <!-- 두 컬럼 레이아웃 -->
      <main class="main-row">
        <!-- LEFT: 웨이퍼 선택 + 웨이퍼 맵 -->
        <section class="left-column">
          <!-- 네비게이션을 웨이퍼 맵 바로 위로 -->
          <div class="wafer-nav">
            <button class="nav-button" on:click={prev}>&lt;</button>

            <div class="wafer-label">
              Wafer {currentWafer.wafer}
              <span class="wafer-lot">(Lot {currentWafer.lot})</span>
              <span class="wafer-index">
                {currentIndex + 1} / {wafers.length}
              </span>
            </div>

            <button class="nav-button" on:click={next}>&gt;</button>
          </div>

          <!-- 실제 웨이퍼 맵 패널 -->
          <WaferMapPanel wafer={currentWafer} />
        </section>

        <!-- RIGHT: 피어슨 상관계수 패널 -->
        <section class="right-column">
          <TrendCorrelationPanel
            targetName={corrTargetName}
            {correlations}
          />
        </section>
      </main>
    {/if}
  </div>
</div>

<style>
  .wafer-page-root {
    min-height: 480px;
    background-color: #ffffff;
    display: flex;
    flex-direction: column;
  }

  .status-message {
    padding: 4px 20px;
    font-size: 12px;
    color: #4b5563;
  }

  .content-area {
    padding: 16px 32px 40px;
  }

  .text-muted {
    color: #9ca3af;
    font-size: 0.875rem;
  }

  .text-error {
    color: #ef4444;
    font-size: 0.875rem;
  }

  .page-header {
    margin-bottom: 12px;
  }

  .page-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #111827;
  }

  /* === 레이아웃 === */
  .main-row {
    display: flex;
    align-items: flex-start;
    gap: 20px;
  }

  .left-column {
    flex: 0 0 auto;
    min-width: 560px;
  }

  .right-column {
    flex: 0 0 420px;
    max-width: 420px;
  }

  /* === 네비게이션 부분 (간격 줄인 버전) === */
  .wafer-nav {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;             /* 버튼 ↔ 텍스트 간격 (스페이스 4칸 정도) */
    margin-bottom: 12px;
  }

  .nav-button {
    padding: 4px 8px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: #ffffff;
    cursor: pointer;
  }

  .nav-button:hover {
    background-color: #f3f4f6;
  }

  .wafer-label {
    /* flex:1 없애고 내용 크기만큼만 차지하게 */
    flex: 0 0 auto;
    text-align: center;
    font-size: 0.9rem;
  }

  .wafer-lot {
    color: #6b7280;
    margin-left: 4px;
  }

  .wafer-index {
    margin-left: 8px;
    font-size: 11px;
    color: #9ca3af;
  }

  @media (max-width: 1200px) {
    .main-row {
      flex-direction: column;
    }

    .left-column,
    .right-column {
      min-width: 0;
      width: 100%;
      flex: 1 1 auto;
    }
  }
</style>
