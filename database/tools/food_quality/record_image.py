"""Record an explicitly generated AI illustration and encode an isolated staging WebP."""
import hashlib
import json
from pathlib import Path
import re
import sys
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[3]
STAGING = ROOT / "database/staging/food-quality-v1"

def record(payload):
    ref = payload["recipe_ref"]
    if not re.fullmatch(r"R0(?:3[1-9]|[45][0-9]|60)", ref):
        raise ValueError("Only new recipe illustration references allowed")
    jobs_path = STAGING / "image-generation-jobs.json"
    jobs = json.loads(jobs_path.read_text(encoding="utf-8"))
    job = next(r for r in jobs["recipes"] if r["recipe_ref"] == ref)
    source = Path(payload["source_path"]).resolve()
    allowed = Path.home() / ".codex/generated_images"
    if not source.is_relative_to(allowed.resolve()) or not source.is_file():
        raise ValueError("Expected a generated image artifact")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    destination = STAGING / "images" / job["filename"]
    if destination.exists() and job.get("original_sha256") != digest:
        raise ValueError("Refusing to replace an existing illustration without review")
    with Image.open(source) as original:
        original.load()
        original_dimensions = list(original.size)
        # Output format/aspect explicitly requested; does not alter depicted ingredients.
        encoded = ImageOps.fit(original.convert("RGB"), (800, 450), method=Image.Resampling.LANCZOS)
        destination.parent.mkdir(parents=True, exist_ok=True)
        encoded.save(destination, "WEBP", quality=82, method=6)
    with Image.open(destination) as check:
        check.load()
        if check.format != "WEBP" or check.size != (800, 450):
            raise ValueError("Invalid encoded illustration")
    job.update(status="GENERATED_PENDING_VISUAL_REVIEW", tool="built-in image_gen", generated_date="2026-10-19",
        prompt=payload.get("prompt", job["prompt"]), original_artifact_name=source.name,
        original_sha256=digest, original_dimensions=original_dimensions,
        staging_path=destination.relative_to(ROOT).as_posix(), width=800, height=450,
        sha256=hashlib.sha256(destination.read_bytes()).hexdigest(), bytes=destination.stat().st_size,
        source_rights="Original AI-generated illustration via authorized built-in tool; not third-party photography",
        disclosure="Ảnh minh họa AI, không phải ảnh chụp suất đã cân đo", image_url=None,
        production_approved=False)
    jobs_path.write_text(json.dumps(jobs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(ref + " staged WebP800x450; runtime URL remains unset")

if __name__ == "__main__":
    record(json.load(sys.stdin))
