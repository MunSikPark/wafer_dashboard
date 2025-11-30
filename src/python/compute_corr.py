# C:\Users\munsikpark\wafer_dashboard\src\python\compute_corr.py
from __future__ import annotations
from pathlib import Path
import csv
import sys
import math
import json
from typing import Dict, List, Tuple

BASE_DIR = Path(r"C:\Users\munsikpark")  # wafer 폴더들이 있는 위치
TOP_N = 30  # 상위 몇 개만 반환할지


def die_key(
    lot_id: str,
    wafer_id: str,
    head: str,
    site: str,
    x: str,
    y: str,
) -> str:
    """die를 유니크하게 식별하기 위한 key."""
    return "|".join([lot_id, wafer_id, head, site, x, y])


def check_target_in_unique(
    mode: str,
    target_name: str,
    wafer_names: List[str],
) -> bool:
    """
    UNIQUE_TREND.csv / UNIQUE_SERIES.csv 에 target_name 이
    하나라도 존재하는지 빠르게 검사.
    """
    unique_file_name = "UNIQUE_TREND.csv" if mode == "trend" else "UNIQUE_SERIES.csv"

    for w in wafer_names:
        unique_path = BASE_DIR / w / unique_file_name
        if not unique_path.exists():
            continue

        with unique_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            # 헤더는 ["test_name"] 이라고 가정
            for row in reader:
                if not row:
                    continue
                if row[0] == target_name:
                    return True

    return False


def build_target_map(
    mode: str,
    target_name: str,
    wafer_names: List[str],
) -> Dict[str, float]:
    """
    TREND_DATA.csv 또는 SERIES_DATA.csv를 읽어
    target_name 에 해당하는 값만 모아서
    die_key -> value 딕셔너리로 만든다.
    """
    target_map: Dict[str, float] = {}

    data_file_name = "TREND_DATA.csv" if mode == "trend" else "SERIES_DATA.csv"

    for w in wafer_names:
        data_path = BASE_DIR / w / data_file_name
        if not data_path.exists():
            # 생성 안 된 lot은 조용히 스킵
            continue

        with data_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                continue

            # 컬럼 인덱스 찾기
            try:
                idx_lot = header.index("lot_id")
                idx_wafer = header.index("wafer_id")
                idx_head = header.index("head")
                idx_site = header.index("site")
                idx_x = header.index("x")
                idx_y = header.index("y")
                idx_test = header.index("test_name")
                idx_val = header.index("value_raw")
            except ValueError:
                # 헤더 이상하면 그냥 스킵
                continue

            for row in reader:
                if not row:
                    continue
                if row[idx_test] != target_name:
                    continue

                # 숫자 변환 실패하면 스킵
                try:
                    v = float(row[idx_val])
                except ValueError:
                    continue

                k = die_key(
                    row[idx_lot],
                    row[idx_wafer],
                    row[idx_head],
                    row[idx_site],
                    row[idx_x],
                    row[idx_y],
                )
                target_map[k] = v

    return target_map


def accumulate_stats(
    mode: str,
    target_name: str,
    wafer_names: List[str],
    target_map: Dict[str, float],
):
    """
    target_map (die_key -> target value)를 기준으로
    나머지 모든 테스트들에 대한 통계량(n, sum_x, sum_y, sum_x2, sum_y2, sum_xy)을 쌓는다.
    """
    data_file_name = "TREND_DATA.csv" if mode == "trend" else "SERIES_DATA.csv"

    # test_name -> [n, sum_x, sum_y, sum_x2, sum_y2, sum_xy]
    stats: Dict[str, List[float]] = {}

    for w in wafer_names:
        data_path = BASE_DIR / w / data_file_name
        if not data_path.exists():
            continue

        with data_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                continue

            try:
                idx_lot = header.index("lot_id")
                idx_wafer = header.index("wafer_id")
                idx_head = header.index("head")
                idx_site = header.index("site")
                idx_x = header.index("x")
                idx_y = header.index("y")
                idx_test = header.index("test_name")
                idx_val = header.index("value_raw")
            except ValueError:
                continue

            for row in reader:
                if not row:
                    continue

                test = row[idx_test]
                if test == target_name:
                    # 자기 자신과의 상관은 별로 의미 없으니 건너뛰자
                    continue

                k = die_key(
                    row[idx_lot],
                    row[idx_wafer],
                    row[idx_head],
                    row[idx_site],
                    row[idx_x],
                    row[idx_y],
                )

                # target 값이 없는 die는 스킵
                x = target_map.get(k)
                if x is None:
                    continue

                try:
                    y = float(row[idx_val])
                except ValueError:
                    continue

                stat = stats.get(test)
                if stat is None:
                    # n, sum_x, sum_y, sum_x2, sum_y2, sum_xy
                    stat = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                    stats[test] = stat

                stat[0] += 1.0          # n
                stat[1] += x            # sum_x
                stat[2] += y            # sum_y
                stat[3] += x * x        # sum_x2
                stat[4] += y * y        # sum_y2
                stat[5] += x * y        # sum_xy

    return stats


def compute_corr_from_stats(
    stats: Dict[str, List[float]],
    min_n: int = 3,
) -> List[Dict[str, float]]:
    """
    stats 딕셔너리로부터 Pearson r 계산.
    """
    results = []

    for name, (n, sx, sy, sx2, sy2, sxy) in stats.items():
        n_int = int(n)
        if n_int < min_n:
            continue

        mean_x = sx / n
        mean_y = sy / n

        cov = sxy / n - mean_x * mean_y
        var_x = sx2 / n - mean_x * mean_x
        var_y = sy2 / n - mean_y * mean_y

        if var_x <= 0 or var_y <= 0:
            continue

        denom = math.sqrt(var_x * var_y)
        if denom == 0:
            continue

        r = cov / denom

        # 혹시 수치적 문제로 NaN/inf 나오면 버림
        if not math.isfinite(r):
            continue

        results.append(
            {
                "name": name,
                "corr": r,
                "count": n_int,
            }
        )

    # |r| 기준 내림차순 정렬 후 TOP_N
    results.sort(key=lambda d: abs(d["corr"]), reverse=True)
    return results[:TOP_N]


def main():
    """
    사용 예:
      python compute_corr.py trend GROSSICC 4174991.081.4991-06.FPP.00 4174991.081.4991-07.FPP.00
      python compute_corr.py series FINAL_BLOCK_BINS 4174991.081.4991-06.FPP.00
    """
    if len(sys.argv) < 4:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Usage: python compute_corr.py <trend|series> <target_name> <wafer_name1> [<wafer_name2> ...]",
                },
                ensure_ascii=False,
            )
        )
        return

    mode = sys.argv[1].strip().lower()      # "trend" or "series"
    target_name = sys.argv[2].strip()
    wafer_names = [w.strip() for w in sys.argv[3:] if w.strip()]

    if mode not in ("trend", "series"):
        print(
            json.dumps(
                {"ok": False, "error": "mode must be 'trend' or 'series'"},
                ensure_ascii=False,
            )
        )
        return

    if not wafer_names:
        print(
            json.dumps(
                {"ok": False, "error": "wafer_names is empty"},
                ensure_ascii=False,
            )
        )
        return

    # 1) UNIQUE_* 에서 target 있는지 먼저 체크 (빠름)
    exists_in_unique = check_target_in_unique(mode, target_name, wafer_names)
    if not exists_in_unique:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"선택한 테스트 '{target_name}' 는 지정한 lot들(wafer 폴더) 의 UNIQUE_{mode.upper()} 에 존재하지 않습니다.",
                },
                ensure_ascii=False,
            )
        )
        return

    # 2) TREND_DATA / SERIES_DATA 에서 실제 값 모으기
    target_map = build_target_map(mode, target_name, wafer_names)

    if not target_map:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"선택한 테스트 '{target_name}' 에 대한 실측 데이터가 어떤 lot의 {mode.upper()}_DATA.csv 에도 존재하지 않습니다.",
                },
                ensure_ascii=False,
            )
        )
        return

    # 3) 전체 테스트에 대한 통계량 쌓기
    stats = accumulate_stats(mode, target_name, wafer_names, target_map)

    if not stats:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"'{target_name}' 와 상관관계를 계산할 다른 테스트 데이터가 충분하지 않습니다.",
                },
                ensure_ascii=False,
            )
        )
        return

    # 4) Pearson r 계산
    correlations = compute_corr_from_stats(stats, min_n=3)

    if not correlations:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"'{target_name}' 와 유의미한 상관관계를 가진 테스트를 찾지 못했습니다.",
                },
                ensure_ascii=False,
            )
        )
        return

    # 5) 결과 JSON 출력
    out = {
        "ok": True,
        "mode": mode,
        "target": target_name,
        "wafer_names": wafer_names,
        "correlations": correlations,
    }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
