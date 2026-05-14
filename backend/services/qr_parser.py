# backend/services/qr_parser.py

from pyzbar.pyzbar import decode
from PIL import Image
from urllib.parse import urlparse, parse_qs
import re


# -------------------------------
# UPI FIELD MAP
# -------------------------------
UPI_FIELDS = {
    "pa": "upi_id",
    "pn": "name",
    "am": "amount",
    "cu": "currency",
    "tn": "note",
    "tr": "transaction_ref"
}


# -------------------------------
# VALIDATION
# -------------------------------
def is_valid_upi(upi):
    return bool(re.match(r"^[a-zA-Z0-9._-]{2,}@[a-zA-Z]{2,}$", upi or ""))


# -------------------------------
# PARSE UPI STRING
# -------------------------------
def parse_upi_string(qr_data):
    parsed = {
        "type": "UNKNOWN",
        "raw": qr_data,
        "fields": {}
    }

    if not qr_data:
        return parsed

    if qr_data.startswith("upi://"):
        parsed["type"] = "UPI"

        try:
            url = urlparse(qr_data)
            params = parse_qs(url.query)

            for key, value in params.items():
                field_name = UPI_FIELDS.get(key, key)
                parsed["fields"][field_name] = value[0] if value else ""

        except Exception:
            pass

    return parsed


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def parse_upi_qr(image_path):
    try:
        image = Image.open(image_path)
        decoded_objects = decode(image)

        if not decoded_objects:
            return {
                "success": False,
                "message": "No QR code detected",
                "data": []
            }

        results = []

        for obj in decoded_objects:
            try:
                qr_data = obj.data.decode("utf-8", errors="ignore").strip()
            except Exception:
                continue

            parsed = parse_upi_string(qr_data)

            # -------------------------------
            # VALIDATION + FLAGS
            # -------------------------------
            flags = []

            upi_id = parsed["fields"].get("upi_id")

            if upi_id and not is_valid_upi(upi_id):
                flags.append("Invalid UPI ID format")

            if not upi_id:
                flags.append("Missing UPI ID")

            amount = parsed["fields"].get("amount")
            if amount:
                try:
                    amt = float(amount)
                    if amt > 100000:
                        flags.append("Unusually high amount")
                except:
                    flags.append("Invalid amount format")

            # -------------------------------
            # BUILD RESULT
            # -------------------------------
            results.append({
                "raw": qr_data,
                "parsed": parsed,
                "flags": flags,
                "suspicious": len(flags) > 0
            })

        return {
            "success": True,
            "count": len(results),
            "data": results
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": []
        }