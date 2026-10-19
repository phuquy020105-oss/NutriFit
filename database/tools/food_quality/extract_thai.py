"""Offline extraction of hash-pinned INMU Thai FCD public detail pages; no zero filling."""
from decimal import Decimal
from html.parser import HTMLParser
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urlparse, parse_qs

KEYS = {"Protein, total": ("protein_per_100g", "g"), "Fat, total": ("fat_per_100g", "g"),
    "Carbohydrate, available": ("carbs_per_100g", "g"), "Dietary fibre": ("fiber_per_100g", "g")}

class Tables(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self, tag, attrs):
        if tag == "tr": self.row=[]
        if tag in ("td", "th") and self.row is not None: self.cell=[]
    def handle_data(self, value):
        if self.cell is not None: self.cell.append(value)
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split())); self.cell=None
        if tag == "tr" and self.row is not None: self.rows.append(self.row); self.row=None

def number(raw):
    if raw.strip() in ("", "-", "Tr", "trace", "N/A"): return None
    value=Decimal(raw)
    if not value.is_finite() or value < 0: raise ValueError("Invalid INMU nutrient amount")
    return format(value, "f")

def field(page, label):
    found=re.search(re.escape(label)+r"\s*</div>\s*<div[^>]*>(.*?)</div>",page,re.S)
    if not found: raise ValueError("Missing INMU identity field: "+label)
    return " ".join(html.unescape(re.sub(r"<[^>]+>"," ",found.group(1))).split())

def extract_page(page, metadata):
    url=urlparse(metadata["url"])
    if (url.scheme != "https" or url.hostname != "inmu.mahidol.ac.th" or url.username or url.password
            or parse_qs(url.query).get("selected_id") != [metadata["record_id"]]
            or parse_qs(url.query).get("selected_dbcode") != ["STD"]):
        raise ValueError("INMU record/URL mismatch")
    if "Per 100 g edible portion" not in page: raise ValueError("Unverified INMU mass basis")
    if field(page,"English name:") != metadata["source_description"]: raise ValueError("INMU identity mismatch")
    parser=Tables(); parser.feed(page)
    all_rows={}
    for row in parser.rows:
        if row and row[0] in {*KEYS,"Energy, by calculation","Total energy - by calculation","Moisture","Ash"}:
            if len(row)!=10 or row[0] in all_rows: raise ValueError("Unexpected/duplicate INMU nutrient row")
            all_rows[row[0]]=row
    nutrients={}
    selected=dict(KEYS)
    # The source has two differently named energy fields. Preserve which one supplied the value.
    energy=next((n for n in ("Energy, by calculation","Total energy - by calculation")
        if n in all_rows and number(all_rows[n][2]) is not None),None)
    if energy: selected[energy]=("calories_per_100g","kcal")
    for label,(key,unit) in selected.items():
        row=all_rows.get(label)
        if row is None: raise ValueError("INMU nutrient row missing; do not invent a column")
        if row[1]!=unit: raise ValueError("Unexpected INMU nutrient unit")
        nutrients[key]=dict(value=number(row[2]),original_text=row[2],unit="KCAL" if unit=="kcal" else "G",
            source_nutrient_name=label,derivation=dict(description=row[3]),sample_n=row[4],minimum=row[5],
            maximum=row[6],standard_deviation=row[7],footnote=row[8],source_last_updated=row[9],
            basis="100 g edible portion")
    if not energy:
        nutrients["calories_per_100g"]=dict(value=None,original_text="-",unit="KCAL",basis="100 g edible portion",
            source_nutrient_name="Neither source energy field is quantified",derivation={})
    return dict(source="Institute of Nutrition, Mahidol University, Thailand (INMU)",
        source_url=metadata["url"],record_id=metadata["record_id"],food_code=field(page,"Food Code:"),
        description=metadata["source_description"],scientific_name=field(page,"Scientific name:"),
        release="Online Thai FCD STD; individual nutrient update/derivation retained, snapshot2026-10-19",
        retrieved_date=metadata["retrieved_date"],page_sha256=metadata["sha256"],nutrients=nutrients,
        auxiliary_rows={k:all_rows[k] for k in ("Moisture","Ash") if k in all_rows})

def extract(cache):
    cache=Path(cache)
    # Reviewed record metadata comes from Git, not a mutable cache index.
    metadata=json.loads((Path(__file__).resolve().parents[3]/"database/staging/food-quality-v1/thai-source-records.json").read_text(encoding="utf-8"))
    result={}
    for row in metadata["records"]:
        path=cache/row["file"]
        if path.resolve().parent != cache.resolve(): raise ValueError("Unsafe INMU source path")
        payload=path.read_bytes()
        if hashlib.sha256(payload).hexdigest()!=row["sha256"]: raise ValueError("INMU source checksum mismatch")
        if row["record_id"] in result: raise ValueError("Duplicate INMU record")
        result[row["record_id"]]=extract_page(payload.decode("utf-8-sig"),row)
    return result

def normalize(key, record, confidence="MODERATE"):
    nutrient=record["nutrients"][key]
    if nutrient["value"] is None:
        return dict(value=None,status="MISSING",confidence="NONE",method="INMU missing/trace is not zero")
    description=(nutrient.get("derivation") or {}).get("description","")
    lower=description.lower()
    status="ESTIMATED" if any(t in lower for t in ("assum","estimat","imput")) else (
        "CALCULATED" if "calculat" in lower or key=="calories_per_100g" else "MATCHED")
    return dict(value=nutrient["value"],status=status,confidence="LOW" if status=="ESTIMATED" else confidence,
        method=("INMU available carbohydrate used directly, NOT total minus fiber again; " if key=="carbs_per_100g" else
                "INMU published value; ")+(description or "derivation not published; no claim of analytical verification"))
