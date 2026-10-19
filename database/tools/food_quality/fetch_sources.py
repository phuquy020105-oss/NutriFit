"""Fetch only reviewed public source URLs, or verify cache offline. No database/config access."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import time
import urllib.parse
import urllib.request

MANIFEST=Path(__file__).resolve().parents[3]/"database/staging/food-quality-v1/source-retrieval-manifest.json"
HOSTS={"fdc.nal.usda.gov","www.mext.go.jp","viendinhduong.vn"}


def safe_target(cache, relative):
    rel=PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts or ":" in relative or "\\" in relative:
        raise ValueError("Unsafe source cache path")
    root=Path(cache).resolve()
    target=(root / Path(*rel.parts)).resolve()
    if not target.is_relative_to(root) or target==root:
        raise ValueError("Source cache path escapes destination")
    return target


def verify_file(path, expected):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:
        raise ValueError("Source checksum mismatch; stop for source review, never silently overwrite")


def run(cache, download=False):
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    cache=Path(cache)
    nin=[]
    for row in manifest["files"]:
        url=urllib.parse.urlparse(row["url"])
        if url.scheme!="https" or url.hostname not in HOSTS or url.username or url.password:
            raise ValueError("Only reviewed credential-free official HTTPS sources allowed")
        destination=safe_target(cache,row["file"])
        if not destination.exists():
            if not download:
                raise ValueError("Reviewed source missing; use --download-missing explicitly")
            # Standard verified HTTPS only. A403/DNS/TLS error stops; no access-control bypass.
            with urllib.request.urlopen(row["url"],timeout=45) as response:
                payload=response.read()
            if hashlib.sha256(payload).hexdigest()!=row["sha256"]:
                raise ValueError("Upstream source changed; review source before replacing manifest")
            destination.parent.mkdir(parents=True,exist_ok=True)
            with destination.open("xb") as out:
                out.write(payload)
            time.sleep(1)
        verify_file(destination,row["sha256"])
        if row["file"].startswith("nin-searches/"):
            nin.append(dict(row,file=PurePosixPath(row["file"]).name))
    index=safe_target(cache,"nin-searches/retrieval-index.json")
    if index.exists():
        if json.loads(index.read_text(encoding="utf-8"))!=nin:
            raise ValueError("NIN retrieval index differs from reviewed manifest")
    elif download:
        index.parent.mkdir(parents=True,exist_ok=True)
        index.write_text(json.dumps(nin,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    else:
        raise ValueError("NIN retrieval index missing")
    print("VERIFIED",len(manifest["files"]),"reviewed source files; no database access")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--download-missing",action="store_true")
    args=parser.parse_args()
    run(args.cache,args.download_missing)
