from pathlib import Path
import csv
import re

# 원시 데이터 위치
RAW_PATH = Path(r"C:\Users\munsikpark\4174991.081.4991-06.FPP.00.csv")

# 필터 규칙 (원래처럼 문자열로 유지)
VSOA_PREFIX = "VSOA_"
PGP_SUFFIX = "_PGP"

# 정규식 미리 컴파일
TEST_NAME_RE = re.compile(r"[A-Z0-9_]+$")
HEAD_SITE_XY_RE = re.compile(
    r'Head\((?P<head>-?\d+)\)\s+Site\((?P<site>-?\d+)\)\s+\(X,Y\)=\((?P<x>-?\d+),(?P<y>-?\d+)\)'
)


def parse_lot_wafer_from_filename(path: Path):
    """
    예: 4174991.081.4991-06.FPP.00.csv
      -> lot_id = 4174991.081.4991
      -> wafer_id = 06
    포맷이 다르면 여기만 수정하면 됨.
    """
    name = path.name  # 4174991.081.4991-06.FPP.00.csv
    base = name[:-4]  # remove .csv
    # 4174991.081.4991-06.FPP.00
    before_fpp = base.split(".FPP", 1)[0]  # 4174991.081.4991-06
    lot_part, wafer_part = before_fpp.split("-")
    return lot_part, wafer_part


def is_valid_test_name(token: str) -> bool:
    """
    메타에 정의된 이름들 중에서 테스트 이름으로 볼 후보.
    대충 '대문자/숫자/언더스코어' 로 제한.
    (정규식 미리 컴파일해서 사용)
    """
    return TEST_NAME_RE.fullmatch(token) is not None


def is_nan_value(v: str) -> bool:
    """
    trend value가 NaN인 경우 필터하기 위한 함수.
    'NaN', 'nan', 'NAN', '-nan', '-NaN', '-NAN' 모두 True.
    공백은 없다고 가정(value_raw는 split 후 문자열).
    """
    # leading sign 제거
    if v.startswith('-'):
        v = v[1:]

    if len(v) != 3:
        return False

    c0, c1, c2 = v[0], v[1], v[2]
    return (c0 in ('N', 'n')) and (c1 in ('A', 'a')) and (c2 in ('N', 'n'))


def collect_meta_defs(raw_path: Path):
    """
    메타데이터 영역(첫 "Head(" 나오기 전까지)을 스캔해서:

    - TREND_DEF 에 정의된 테스트 이름들 set
    - SERIES_DEF 에 정의된 테스트 이름들 set
    - time_profiler 가 포함된 메타 줄들 리스트

    를 반환한다.

    공통 필터:
      - 라인에 print_memory_usage 있으면 완전 무시
      - 테스트 이름이 VSOA_ 시작 / _PGP 끝이면 버림
    """
    trend_names = set()
    series_names = set()
    time_profiler_lines = []

    with raw_path.open("r", encoding="utf-8", errors="ignore") as f:
        trend_add = trend_names.add
        series_add = series_names.add
        is_valid = is_valid_test_name
        vsoa_prefix = VSOA_PREFIX
        pgp_suffix = PGP_SUFFIX

        for line in f:
            # die-level 데이터 시작하면 meta 영역 끝
            if '"Head(' in line:
                break

            if "print_memory_usage" in line:
                continue

            # time_profiler 메타 라인 수집
            if "time_profiler" in line:
                time_profiler_lines.append(line.rstrip("\n"))

            # TREND_DEF / SERIES_DEF 파싱
            if "TREND_DEF" not in line and "SERIES_DEF" not in line:
                continue

            tokens = line.strip().split()
            kind = None
            start_idx = 0

            # TREND_DEF / SERIES_DEF 위치 먼저 찾기
            for i, t in enumerate(tokens):
                if t == "TREND_DEF":
                    kind = "TREND"
                    start_idx = i + 1
                    break
                elif t == "SERIES_DEF":
                    kind = "SERIES"
                    start_idx = i + 1
                    break

            if kind is None:
                continue  # 못 찾으면 패스

            # ★ 수정 포인트: '첫 번째 유효 토큰'만 이름으로 사용
            name_token = None
            for token in tokens[start_idx:]:
                if is_valid(token):
                    name_token = token
                    break

            if not name_token:
                continue

            # VSOA_ / _PGP 필터
            if name_token.startswith(vsoa_prefix) or name_token.endswith(pgp_suffix):
                continue

            if kind == "TREND":
                trend_add(name_token)
            else:  # kind == "SERIES"
                series_add(name_token)

    return trend_names, series_names, time_profiler_lines


def parse_head_site_xy(line: str):
    """
    예: "Head(0) Site(60) (X,Y)=(-7,4)"
    에서 head, site, x, y 추출.
    """
    m = HEAD_SITE_XY_RE.search(line)
    if not m:
        return None, None, None, None
    return int(m.group("head")), int(m.group("site")), int(m.group("x")), int(m.group("y"))


def process_die_data(raw_path: Path, trend_names, series_names, timeprof_path: Path,
                     trend_out_path: Path, series_out_path: Path,
                     lot_id: str, wafer_id: str):
    """
    원시 파일 전체를 다시 스캔하면서:

      - die 블록("Head(" ~ "Bin Results"/"}")을 순회
      - 각 다이에 대해:
          trend_names, series_names 에 해당하는 key 라인의 값들을 추출
      - time_profiler 가 포함된 모든 라인은 별도 파일에 기록

    출력:
      - trend_out_path : CSV (lot_id, wafer_id, head, site, x, y, test_name, value_raw)
      - series_out_path: CSV (동일 형식)
      - timeprof_path  : txt (line 그대로)
    """

    vsoa_prefix = VSOA_PREFIX
    pgp_suffix = PGP_SUFFIX

    with raw_path.open("r", encoding="utf-8", errors="ignore") as fin, \
         trend_out_path.open("w", newline="", encoding="utf-8") as f_trend, \
         series_out_path.open("w", newline="", encoding="utf-8") as f_series, \
         timeprof_path.open("a", encoding="utf-8") as f_tprof:  # 메타에서 이미 쓴 것 이어쓰기

        trend_writer = csv.writer(f_trend)
        series_writer = csv.writer(f_series)

        trow = trend_writer.writerow
        srow = series_writer.writerow
        tprof_write = f_tprof.write

        trend_set = trend_names
        series_set = series_names

        # 헤더
        header = ["lot_id", "wafer_id", "head", "site", "x", "y", "test_name", "value_raw"]
        trow(header)
        srow(header)

        in_meta = True
        head = site = x = y = None

        for line in fin:
            s = line.rstrip("\n")

            # 메타 부분 처리
            if in_meta:
                if '"Head(' in s:
                    in_meta = False
                    head, site, x, y = parse_head_site_xy(s)
                else:
                    # meta 구간에서도 time_profiler 라인 수집
                    if "time_profiler" in s and "print_memory_usage" not in s:
                        if vsoa_prefix not in s and pgp_suffix not in s:
                            tprof_write(s + "\n")
                continue

            # 여기부터는 die-level 데이터

            # 새 die 블록 시작
            if '"Head(' in s:
                head, site, x, y = parse_head_site_xy(s)
                continue

            # time_profiler 라인 수집 (die 영역)
            if "time_profiler" in s and "print_memory_usage" not in s:
                if vsoa_prefix not in s and pgp_suffix not in s:
                    tprof_write(s + "\n")

            # 블록 종료(대략) – 특별히 할 건 없음, head/site/x/y는 다음 Head 만나면 갱신
            if s == "}" or s.startswith("Bin Results"):
                continue

            # 완전 빈 줄
            if not s:
                continue

            # continuation 라인(앞에 공백) → 여기서는 값 전체를 한 덩어리로 쓰지 않을 거라서 스킵
            if s[0].isspace():
                continue

            # key + values 구조 라인
            parts = s.split(maxsplit=1)
            if not parts:
                continue
            key = parts[0]
            value_raw = parts[1] if len(parts) > 1 else ""

            # 공통 필터
            if key.startswith(vsoa_prefix) or key.endswith(pgp_suffix):
                continue
            if "print_memory_usage" in s:
                continue

            # TREND (NaN / -NaN 값은 저장하지 않음)
            if key in trend_set:
                if not is_nan_value(value_raw):
                    trow([
                        lot_id, wafer_id,
                        head, site, x, y,
                        key, value_raw
                    ])

            # SERIES
            if key in series_set:
                srow([
                    lot_id, wafer_id,
                    head, site, x, y,
                    key, value_raw
                ])


def main():
    raw_path = RAW_PATH
    lot_id, wafer_id = parse_lot_wafer_from_filename(raw_path)

    base = raw_path.with_suffix("")  # ...\4174991.081.4991-06.FPP.00
    trend_out = base.with_name(base.name + "_TREND_DATA.csv")
    series_out = base.with_name(base.name + "_SERIES_DATA.csv")
    timeprof_out = base.with_name(base.name + "_TIME_PROFILER.txt")

    print(f"Raw file:            {raw_path}")
    print(f"Lot / Wafer:         {lot_id} / {wafer_id}")
    print(f"TREND data out:      {trend_out}")
    print(f"SERIES data out:     {series_out}")
    print(f"TIME_PROFILER out:   {timeprof_out}")

    # 1) 메타에서 TREND_DEF / SERIES_DEF / time_profiler 수집
    trend_names, series_names, timeprof_meta_lines = collect_meta_defs(raw_path)

    # time_profiler 메타 라인 먼저 기록
    with timeprof_out.open("w", encoding="utf-8") as f:
        for line in timeprof_meta_lines:
            f.write(line + "\n")

    print(f"Collected {len(trend_names)} TREND_DEF names, {len(series_names)} SERIES_DEF names.")

    # 2) die-level 데이터에서 해당 이름들만 추출
    process_die_data(
        raw_path,
        trend_names,
        series_names,
        timeprof_out,
        trend_out,
        series_out,
        lot_id,
        wafer_id,
    )

    print("Done.")


if __name__ == "__main__":
    main()
