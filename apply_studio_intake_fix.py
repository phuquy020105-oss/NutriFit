# -*- coding: utf-8 -*-
"""Apply a narrow, version-safe idempotency fix to NutriFit frontend/js/studio.js.

Run from NutriFit-UI root:
    python apply_studio_intake_fix.py --check
    python apply_studio_intake_fix.py --apply

This script refuses unfamiliar versions rather than overwriting the whole UI.
"""
from __future__ import annotations
import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NEW_JS = '''const payload={confirmed:true,mealType:state.mealType,
      meal:{optionId:option.optionId,revision:m.revision},
      items:parts.map(part=>({dish_id:part.dish_id,grams:part.grams}))};
    // Same exact meal request -> same key; a changed menu -> a new key.
    // Back end still verifies ownership, revision and actual nutrition.
    if(!globalThis.crypto?.subtle){
      node.disabled=false;
      toast('Trình duyệt chưa hỗ trợ xác nhận an toàn. Hãy dùng localhost hoặc HTTPS.',true);
      return;
    }
    try{
      const fingerprint=JSON.stringify({userId:id(),day:m.date||today(),...payload});
      const bytes=new TextEncoder().encode(fingerprint);
      const digest=await globalThis.crypto.subtle.digest('SHA-256',bytes);
      const hex=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
      payload.requestId='nfmeal_'+hex.slice(0,48);
    }catch(_error){
      node.disabled=false;
      toast('Không tạo được mã xác nhận bữa ăn. Vui lòng thử lại.',true);
      return;
    }'''


def transform(source: str) -> tuple[str, bool]:
    start = source.find('async function confirmMealIntake(node){')
    if start < 0:
        raise ValueError('Không tìm thấy hàm confirmMealIntake(node). Không ghi đè file.')
    end = source.find('\n  async function ', start + 1)
    if end < 0:
        raise ValueError('Không xác định được ranh giới hàm confirmMealIntake().')
    body = source[start:end]
    if "payload.requestId='nfmeal_'+hex.slice(0,48)" in body:
        return source, False
    pos = body.find('const payload={requestId:`nfmeal_')
    if pos < 0:
        raise ValueError('Mã hiện tại đã khác phiên bản V6. Cần xem đoạn confirmMealIntake trước khi sửa.')
    semi = body.find(';', pos)
    if semi < 0:
        raise ValueError('Không xác định được đối tượng payload.')
    old = body[pos:semi+1]
    if not all(token in old for token in (
        'nfmeal_${id()}_${m.date||today()}_${state.mealType}',
        'confirmed:true', 'mealType:state.mealType',
        'optionId:option.optionId', 'revision:m.revision', 'items:parts.map('
    )):
        raise ValueError('Payload có cấu trúc khác mẫu; không tự sửa để tránh mất code mới.')
    nl = '\r\n' if '\r\n' in source else '\n'
    new_js = NEW_JS.replace('\n', nl)
    new_body = body[:pos] + new_js + body[semi+1:]
    return source[:start] + new_body + source[end:], True


def main() -> int:
    parser = argparse.ArgumentParser(description='Safely fix NutriFit meal intake requestId')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true', help='Check compatibility, make no changes')
    group.add_argument('--apply', action='store_true', help='Write fix with a backup')
    parser.add_argument('--target', default='frontend/js/studio.js', help='Path relative to NutriFit-UI root')
    args = parser.parse_args()
    path = Path(args.target)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        print(f'ERROR: Không tìm thấy {path}')
        return 2
    # newline='' prevents normalizing existing CRLF source files.
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        original = f.read()
    try:
        updated, changed = transform(original)
    except ValueError as exc:
        print(f'ERROR: {exc}')
        return 2
    if not changed:
        print('OK: Đoạn sửa đã có trong studio.js; không cần áp dụng lại.')
        return 0
    if args.check:
        print(f'OK: Tương thích. Có thể sửa đoạn requestId trong {path}')
        return 0
    backup = path.with_suffix('.js.bak-before-intake-fix')
    if backup.exists():
        print(f'ERROR: Bản sao lưu đã tồn tại tại {backup}. Không ghi đè.')
        return 2
    shutil.copy2(path, backup)
    with path.open('w', encoding='utf-8', newline='') as f:
        f.write(updated)
    print('OK: Đã sửa duy nhất đoạn requestId trong studio.js')
    print(f'BACKUP: {backup}')
    print(f'UPDATED: {path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
