"""
범용 이미지 크롭 스크립트
사용법:
  python3 scripts/crop_images.py --company kec

기본값: 상단 100px 제거, 가로 1280px, 세로 최대 1000px 크롭
필요시 --crops 옵션으로 각 이미지별 크롭 영역 직접 지정 가능

예시 (기본 크롭):
  python3 scripts/crop_images.py --company kec

예시 (커스텀 크롭 - left,top,right,bottom 형식, 5개 이미지):
  python3 scripts/crop_images.py --company kec \
    --crops "0,100,1280,1000|0,100,1280,900|0,100,1280,1100|0,100,1280,950|0,50,1280,700"
"""

import sys
import os
import argparse
from PIL import Image


def get_base():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def crop_images(company: str, crops: list[tuple]):
    BASE = get_base()
    TEMP_DIR = os.path.join(BASE, 'images', f'temp_{company}')
    IMG_DIR = os.path.join(BASE, 'images')

    if not os.path.exists(TEMP_DIR):
        print(f"❌ temp 폴더가 없습니다: {TEMP_DIR}")
        print(f"먼저 capture_images.py를 실행하세요.")
        sys.exit(1)

    print(f"\n[{company}] 크롭 시작\n")

    results = []
    for i, crop_box in enumerate(crops, 1):
        src_name = f'{company}_{i}_full.png'
        dst_name = f'{company}_{i}.png'
        src_path = os.path.join(TEMP_DIR, src_name)
        dst_path = os.path.join(IMG_DIR, dst_name)

        if not os.path.exists(src_path):
            print(f"[{i}] ❌ 파일 없음: {src_path}")
            continue

        img = Image.open(src_path)
        w, h = img.size
        print(f"[{i}] 원본: {w}x{h}")

        # 크롭 영역 범위 제한
        left, top, right, bottom = crop_box
        left = max(0, left)
        top = max(0, top)
        right = min(w, right)
        bottom = min(h, bottom)

        cropped = img.crop((left, top, right, bottom))
        cropped.save(dst_path)

        fsize = os.path.getsize(dst_path)
        cw, ch = cropped.size
        print(f"     크롭: {cw}x{ch} → {dst_name} ({fsize:,} bytes)")
        results.append(dst_name)

    print(f"\n✅ 크롭 완료! {len(results)}개 이미지 저장됨")
    print(f"저장 경로: {IMG_DIR}")
    print(f"\n다음 단계: GitHub push")
    print(f"  git add images/")
    print(f"  git commit -m 'Add {company} product images'")
    print(f"  git push origin main")


def parse_crops(crops_str: str) -> list[tuple]:
    """'0,100,1280,1000|0,100,1280,900|...' 형식 파싱"""
    result = []
    for part in crops_str.split('|'):
        vals = [int(x.strip()) for x in part.strip().split(',')]
        if len(vals) != 4:
            raise ValueError(f"크롭 형식 오류: {part} (left,top,right,bottom 필요)")
        result.append(tuple(vals))
    return result


def default_crops(company: str) -> list[tuple]:
    """기본 크롭: 뷰포트 캡처(450px 스크롤 후) 기준, 상단 30px 제거"""
    return [
        (0, 30, 1280, 900),
        (0, 30, 1280, 900),
        (0, 30, 1280, 900),
        (0, 30, 1280, 900),
        (0, 30, 1280, 900),
    ]


def main():
    parser = argparse.ArgumentParser(description='캡처된 이미지 크롭')
    parser.add_argument('--company', required=True, help='회사명 (영문 소문자, 예: kec)')
    parser.add_argument('--crops', default=None,
                        help='크롭 영역 5개 (left,top,right,bottom|... 형식). 미입력시 기본값 사용')
    args = parser.parse_args()

    if args.crops:
        crops = parse_crops(args.crops)
        if len(crops) != 5:
            print(f"❌ 크롭 영역은 정확히 5개여야 합니다. (현재 {len(crops)}개)")
            sys.exit(1)
    else:
        crops = default_crops(args.company)
        print(f"기본 크롭 사용 (상단 100px 제거, 세로 최대 1000~1100px)")

    crop_images(args.company, crops)


if __name__ == '__main__':
    main()
