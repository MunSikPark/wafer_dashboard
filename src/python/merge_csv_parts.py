from pathlib import Path

# 1. 기본 설정
BASE_DIR = Path(r"C:\Users\munsi\Downloads")
BASENAME = "4455451.0C1.5451-05.FPP.00.Mh8KDCmM1Y74G2GyY"
TOTAL_PARTS = 12

def merge_csv_parts():
    part_files = []

    # part1_of12 ~ part12_of12 까지 정확히 지정
    for part in range(1, TOTAL_PARTS + 1):
        folder_name = f"{BASENAME}_part{part}_of{TOTAL_PARTS}"
        file_name = f"{BASENAME}_part{part}_of{TOTAL_PARTS}.csv"

        folder_path = BASE_DIR / folder_name
        file_path = folder_path / file_name

        if not file_path.exists():
            print(f"[경고] 파일을 찾을 수 없습니다: {file_path}")
        else:
            part_files.append(file_path)

    if len(part_files) != TOTAL_PARTS:
        print(f"\n[에러] 찾은 파일 개수({len(part_files)})가 TOTAL_PARTS({TOTAL_PARTS})와 다릅니다.")
        print("위에 경고 난 파일 경로들을 먼저 확인해 주세요.")
        return

    # 출력 파일: 같은 폴더(BASE_DIR)에 merged로 저장
    output_path = BASE_DIR / f"{BASENAME}_merged.csv"

    print("병합할 파일 순서:")
    for i, path in enumerate(part_files, start=1):
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  {i:2d} : {path}  ({size_mb:.1f} MB)")

    # 실제 병합 (단순 이어붙이기)
    with open(output_path, "w", encoding="utf-8", newline="") as out_f:
        for idx, path in enumerate(part_files, start=1):
            print(f"{idx}번째 파일 처리 중: {path}")
            with open(path, "r", encoding="utf-8") as in_f:
                for line in in_f:
                    out_f.write(line)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n완료: 병합된 파일 -> {output_path}")
    print(f"대략 크기: {size_mb:.1f} MB")

if __name__ == "__main__":
    merge_csv_parts()
