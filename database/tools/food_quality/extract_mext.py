"""Read official MEXT English2015 XLSX using stdlib; preserve trace and estimated markers."""
from decimal import Decimal, ROUND_HALF_UP
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

SHA256 = "5c968f1801f706b2970d51599ab2dce6f9e09ff3901fcf1990922960761885fb"
URL = "https://www.mext.go.jp/component/english/__icsFiles/afieldfile/2017/12/25/1374049_1r12_1.xlsx"
METHOD_URL = "https://www.mext.go.jp/component/english/__icsFiles/afieldfile/2017/10/02/1385123_Standard-Table_Chap.1_Prov_1.pdf"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
COLUMNS = {"F": "calories_per_100g", "I": "protein_per_100g", "K": "fat_per_100g",
           "Q": "carbs_per_100g", "U": "fiber_per_100g"}


def parse_amount(raw, energy=False):
    if raw is None or raw in ("-", "－", "–", ""):
        return None, "MISSING"
    estimated = raw.startswith("(") and raw.endswith(")")
    number = raw[1:-1] if estimated else raw
    if number == "Tr":
        return None, "ESTIMATED_TRACE" if estimated else "TRACE_NOT_ZERO"
    value = Decimal(number)
    if not value.is_finite() or value < 0:
        raise ValueError("Invalid MEXT amount")
    # Chapter1 Table14: kcal integer, these macros/fiber one decimal.
    value = value.quantize(Decimal("1") if energy else Decimal("0.1"), rounding=ROUND_HALF_UP)
    return format(value, "f"), "ESTIMATED" if estimated else "PUBLISHED"


def extract(archive):
    archive = Path(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Unreviewed MEXT archive checksum")
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError("MEXT ZIP CRC failure")
        strings = ["".join(x.itertext()) for x in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("s:si", NS)]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        result = {}
        headers = {}
        for row in sheet.findall("s:sheetData/s:row", NS):
            values = {}
            for cell in row:
                value = cell.find("s:v", NS)
                if value is not None:
                    values[re.sub(r"[0-9]", "", cell.get("r"))] = (
                        strings[int(value.text)] if cell.get("t") == "s" else value.text)
            if row.get("r") == "6":
                headers = values
                if values.get("F") != "Energy (kcal)" or values.get("U") != "Dietary fiber, total":
                    raise ValueError("Unexpected MEXT nutrient columns")
            code = values.get("B", "")
            if not re.fullmatch(r"[0-9]{5}", code) or "D" not in values:
                continue
            if code in result:
                raise ValueError("Duplicate MEXT food item")
            nutrients = {}
            for col, key in COLUMNS.items():
                raw = values.get(col)
                normalized, qualifier = parse_amount(raw, energy=col == "F")
                nutrients[key] = dict(value=normalized, original_excel_text=raw,
                    unit="KCAL" if col == "F" else "G", basis="100 g edible portion",
                    source_cell=col + row.get("r"), source_nutrient_name=headers[col],
                    source_qualifier=qualifier, derivation=(dict(description="Estimated by source") if qualifier == "ESTIMATED"
                        else dict(description="Calculated energy (source)") if col == "F" else None),
                    presentation_method_url=METHOD_URL)
            result[code] = dict(source="MEXT Japan English2015, seventh revised edition",
                release="2015; English workbook updated2017-12-27 (not2023 edition)",
                record_id=code, category=values["A"], description=values["D"], source_url=URL,
                archive_sha256=SHA256, retrieved_date="2026-10-19", remarks=values.get("BP"),
                source_row=row.get("r"), nutrients=nutrients)
        if len(result) != 2191:
            raise ValueError("MEXT main table count must be2191; annex is not the same food list")
        return result
