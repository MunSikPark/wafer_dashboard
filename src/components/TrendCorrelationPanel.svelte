<script lang="ts">
  // WaferPage.svelte 에서 전달
  export let waferOptions: string[] = [];

  type CorrItem = {
    name: string;
    r: number;
  };

  let selectedWafer = '';
  let kind: 'trend' | 'series' = 'trend';

  let tests: string[] = [];
  let selectedTest = '';

  let loadingTests = false;
  let loadingCorr = false;
  let errorMsg = '';

  let corrTargetName = '';
  let correlations: CorrItem[] = [];

  // 새로 추가: 부호 필터 (All / + / -)
  let signFilter: 'all' | 'pos' | 'neg' = 'all';

  // waferOptions 가 들어오면 자동으로 첫 개 선택
  $: if (!selectedWafer && waferOptions.length > 0) {
    selectedWafer = waferOptions[0];
  }

  // wafer / kind 가 바뀔 때마다 UNIQUE_* 다시 로딩
  let lastKey = '';
  $: {
    const key = `${selectedWafer}|${kind}`;
    if (key && key !== lastKey) {
      lastKey = key;
      if (selectedWafer) {
        void loadTests();
      }
    }
  }

  async function loadTests() {
    loadingTests = true;
    errorMsg = '';
    tests = [];
    selectedTest = '';
    corrTargetName = '';
    correlations = [];

    try {
      const params = new URLSearchParams({
        waferId: selectedWafer,
        kind
      });
      const res = await fetch(`/api/trends?${params.toString()}`);
      const json = await res.json();

      if (!res.ok) {
        console.error('loadTests error:', json);
        errorMsg = json.error ?? '테스트 목록을 불러오지 못했습니다.';
        return;
      }

      tests = json.tests ?? [];
    } catch (e) {
      console.error(e);
      errorMsg = '테스트 목록을 불러오는 중 오류가 발생했습니다.';
    } finally {
      loadingTests = false;
    }
  }

  async function runCorrelation() {
    errorMsg = '';
    correlations = [];
    corrTargetName = '';

    if (!selectedWafer) {
      errorMsg = 'Lot(wafer)를 먼저 선택해주세요.';
      return;
    }
    if (!selectedTest) {
      errorMsg = 'Trend / Series 를 하나 선택해주세요.';
      return;
    }
    if (!tests.includes(selectedTest)) {
      errorMsg = '목록에 없는 이름입니다. 콤보박스에서 선택해주세요.';
      return;
    }

    loadingCorr = true;
    try {
      const res = await fetch('/api/corr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          waferId: selectedWafer,
          target: selectedTest,
          kind
        })
      });

      const json = await res.json();
      if (!res.ok) {
        console.error('corr error:', json);
        errorMsg = json.error ?? '피어슨 상관계수 계산 중 오류가 발생했습니다.';
        return;
      }

      corrTargetName = json.target;
      correlations = (json.top ?? []).map((x: any) => ({
        name: x.name,
        r: Number(x.r)
      }));

      // 새로 계산했으니 부호 필터는 All로 리셋
      signFilter = 'all';
    } catch (e) {
      console.error(e);
      errorMsg = '피어슨 상관계수 계산 중 오류가 발생했습니다.';
    } finally {
      loadingCorr = false;
    }
  }

  // -1 ~ 1 -> 색상 (파랑~빨강)
  function rToColor(r: number): string {
    const t = (r + 1) / 2; // 0 ~ 1
    const hue = 240 - t * 240; // 240(파랑) -> 0(빨강)
    const light = 50;
    return `hsl(${hue}, 70%, ${light}%)`;
  }

  // 부호 필터 적용된 결과
  $: filteredCorrelations = correlations.length
    ? correlations.filter((c) => {
        if (signFilter === 'pos') return c.r >= 0;
        if (signFilter === 'neg') return c.r <= 0;
        return true; // all
      })
    : [];

  $: maxAbs = filteredCorrelations.length
    ? Math.max(...filteredCorrelations.map((c) => Math.abs(c.r)))
    : 1;
</script>

<div class="panel-root">
  <!-- 상단: 선택 영역 -->
  <div class="card header-card">
    <div class="header-row">
      <div class="header-title">SELECTED {kind === 'trend' ? 'TREND' : 'SERIES'}</div>
      <div class="kind-toggle">
        <button
          type="button"
          class:selected={kind === 'trend'}
          on:click={() => (kind = 'trend')}
        >
          Trend
        </button>
        <button
          type="button"
          class:selected={kind === 'series'}
          on:click={() => (kind = 'series')}
        >
          Series
        </button>
      </div>
    </div>

    <!-- lot / wafer 선택 -->
    <div class="control-row">
      <label class="field">
        <span class="field-label">Lot / Wafer</span>
        <select bind:value={selectedWafer}>
          {#if !waferOptions.length}
            <option value="">(생성된 Lot 없음)</option>
          {:else}
            {#each waferOptions as w}
              <option value={w}>{w}</option>
            {/each}
          {/if}
        </select>
      </label>

      <!-- trend / series 이름 선택 (콤보박스) -->
      <label class="field flex-1">
        <span class="field-label">
          {kind === 'trend' ? 'UNIQUE_TREND' : 'UNIQUE_SERIES'}
        </span>

        <div class="combo-row">
          <input
            list="test-list"
            class="combo-input"
            placeholder="이름 검색 또는 선택..."
            bind:value={selectedTest}
          />
          <datalist id="test-list">
            {#each tests as t}
              <option value={t} />
            {/each}
          </datalist>

          <button type="button" class="apply-btn" on:click={runCorrelation}>
            Apply
          </button>
        </div>
      </label>
    </div>

    {#if loadingTests}
      <div class="sub-text">테스트 목록을 불러오는 중...</div>
    {:else if corrTargetName}
      <div class="sub-text">
        Showing Pearson correlation with
        <span class="highlight">{corrTargetName}</span>
        {' '}({filteredCorrelations.length} tests, top 30)
      </div>
    {:else}
      <div class="sub-text">
        트렌드/시리즈를 선택하고 <span class="highlight">Apply</span> 를 눌러주세요.
      </div>
    {/if}

    {#if errorMsg}
      <div class="error-text">{errorMsg}</div>
    {/if}
  </div>

  <!-- 히트맵 / 결과 영역 -->
  <div class="card heat-card">
    <div class="heat-header">
      <span>Top correlated tests</span>

      <div class="heat-controls">
        <button
          type="button"
          class:selected={signFilter === 'all'}
          on:click={() => (signFilter = 'all')}
        >
          All
        </button>
        <button
          type="button"
          class:selected={signFilter === 'pos'}
          on:click={() => (signFilter = 'pos')}
        >
          +
        </button>
        <button
          type="button"
          class:selected={signFilter === 'neg'}
          on:click={() => (signFilter = 'neg')}
        >
          -
        </button>
        <span class="heat-unit">Pearson r</span>
      </div>
    </div>

    {#if loadingCorr}
      <div class="sub-text">상관계수 계산 중...</div>
    {:else if !filteredCorrelations.length}
      <div class="sub-text">결과가 없습니다.</div>
    {:else}
      <div class="heat-list">
        {#each filteredCorrelations.slice(0, 30) as item}
          <div class="heat-row">
            <div class="heat-name" title={item.name}>
              {item.name}
            </div>
            <div
              class="heat-bar"
              style={`background:${rToColor(item.r)}; opacity:${
                0.25 + 0.75 * (Math.abs(item.r) / maxAbs)
              }`}
            />
            <div class="heat-value">
              {item.r.toFixed(3)}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
/* =========================
   AWS Console 느낌 라이트 테마
   ========================= */

.panel-root {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* 공통 카드 – AWS 콘솔 카드 느낌 */
.card {
  border-radius: 8px;
  border: 1px solid #d1d5db;         /* 연한 회색 보더 */
  background: #ffffff;                /* 완전 흰색 카드 */
  padding: 12px 14px;
  color: #111827;
  font-size: 12px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04); /* 아주 약한 그림자 */
}

.header-card {
  background: #f9fafb;                /* 콘솔 상단 패널 같은 연한 회색 */
  border-color: #d1d5db;
}

.heat-card {
  background: #ffffff;
  border-color: #e5e7eb;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 240px;
}

/* -------------------- 헤더 영역 -------------------- */

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.header-title {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #374151;
}

/* Trend / Series 토글 – 콘솔의 세그먼트 버튼 느낌 */

.kind-toggle {
  display: inline-flex;
  background: #e5e7eb;
  border-radius: 999px;
  padding: 2px;
  gap: 2px;
}

.kind-toggle button {
  border: none;
  padding: 3px 10px;
  font-size: 11px;
  border-radius: 999px;
  background: transparent;
  color: #4b5563;
  cursor: pointer;
}

.kind-toggle button.selected {
  background: #2563eb;  /* AWS 콘솔 버튼 느낌의 파랑 */
  color: #ffffff;
}

/* -------------------- 입력 컨트롤 -------------------- */

.control-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  margin-bottom: 6px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 150px;
}

.field-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6b7280;
}

select {
  height: 28px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: #ffffff;
  color: #111827;
  padding: 0 8px;
  font-size: 12px;
}

select:focus {
  outline: 2px solid #2563eb33;
  border-color: #2563eb;
}

.flex-1 {
  flex: 1;
}

.combo-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.combo-input {
  flex: 1;
  height: 28px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: #ffffff;
  color: #111827;
  padding: 0 8px;
  font-size: 12px;
}

.combo-input::placeholder {
  color: #9ca3af;
}

.combo-input:focus {
  outline: 2px solid #2563eb33;
  border-color: #2563eb;
}

/* Apply 버튼 – AWS 파랑 버튼 느낌 */

.apply-btn {
  height: 28px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid #2563eb;
  background: #2563eb;
  color: #ffffff;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.apply-btn:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

/* -------------------- 안내 / 에러 텍스트 -------------------- */

.sub-text {
  margin-top: 4px;
  font-size: 11px;
  color: #4b5563;
}

.highlight {
  font-weight: 600;
  color: #b45309;
}

.error-text {
  margin-top: 4px;
  font-size: 11px;
  color: #dc2626;
}

/* -------------------- 상단 라벨 / 필터 영역 -------------------- */

.heat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 11px;
  color: #6b7280;
}

.heat-unit {
  font-size: 10px;
  color: #4b5563;
}

/* 만약 All / + / - 버튼 같은 필터를 이미 쓰고 있다면 */
.heat-controls {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.heat-controls button {
  border: none;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 10px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
}

.heat-controls button.selected {
  background: #e5e7eb;
  color: #111827;
}

/* -------------------- 상관계수 리스트 (히트맵 바) -------------------- */

.heat-list {
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.heat-row {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(0, 1.2fr) auto;
  gap: 6px;
  align-items: center;
}

.heat-name {
  font-size: 11px;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.heat-bar {
  height: 10px;
  border-radius: 999px;
  background: #e5e7eb;
  transition: all 0.2s ease;
}

.heat-value {
  width: 3.2rem;
  text-align: right;
  font-size: 11px;
  color: #374151;
  font-variant-numeric: tabular-nums;
}

</style>
