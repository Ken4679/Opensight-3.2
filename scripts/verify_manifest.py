import argparse
import hashlib
import json
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def verify_manifest(staging_dir: Path) -> bool:
    manifest_path = staging_dir / "SECURITY-MANIFEST.json"
    if not manifest_path.exists():
        print("[FAIL] 缺少 SECURITY-MANIFEST.json", file=sys.stderr)
        return False
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for art in data.get("artifacts", []):
        f = staging_dir / art.get("local_path", "")
        if not f.is_file():
            print(f"[FAIL] 清单组件文件不存在: {art.get('local_path')}", file=sys.stderr)
            return False
        real_sha = hashlib.sha256(f.read_bytes()).hexdigest().lower()
        exp_sha = art.get("expected_sha256", "").lower()
        if real_sha != exp_sha:
            print(f"[FAIL] 哈希校验不匹配: {art.get('artifact_name')} (预期: {exp_sha}, 实际: {real_sha})", file=sys.stderr)
            return False
    print("[PASS] 清单全部组件 SHA-256 哈希校验完全一致！")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("staging_dir", type=Path)
    args = parser.parse_args()
    if not verify_manifest(args.staging_dir):
        sys.exit(1)
