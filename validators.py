import os
import re
import requests
from dateutil import parser as date_parser      
from typing import Dict, Tuple, Optional, Any

def parse_dob(dob_str:str) -> Optional[str]:
    try:
        dt = date_parser.parse(dob_str, fuzzy=True).date()
        if dt.year < 1900 or dt.year > 2026:
            return None
        return dt.isoformat()
    except Exception:
        return None

def validate_address_google(addr: Dict[str, str]) -> Tuple[bool, str, Optional[Dict[str, str]]]:
    data: Dict[str, Any] = {}  # <-- ensures data always exists

    try:
        key = os.getenv("GOOGLE_MAPS_API_KEY")  # or however you load it
        if not key:
            return False, "Missing GOOGLE_MAPS_API_KEY env var.", None

        # Build a single-line address string (Google likes this)
        address = f"{addr.get('street','')}, {addr.get('city','')}, {addr.get('state','')} {addr.get('zip','')}".strip()
        if not address or address == ", ,":
            return False, "Address is empty or incomplete.", None

        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": key}

        resp = requests.get(url, params=params, timeout=10)
        # If HTTP itself failed (403, 400, etc.), this will throw:
        resp.raise_for_status()

        data = resp.json()  # <-- assignment happens here

        #print("DEBUG google status:", data.get("status"))
        #print("DEBUG google error_message:", data.get("error_message"))
        #print("DEBUG request address:", address)

        status = data.get("status")
        if status != "OK":
            # return a specific reason instead of generic "invalid"
            return False, f"Google geocoding failed: {status} - {data.get('error_message')}", None

        results = data.get("results", [])
        if not results:
            return False, "Google returned OK but no results.", None

        r0 = results[0]
        formatted = r0.get("formatted_address")
        #print("DEBUG formatted_address:", formatted)

        # Normalize back into your schema (basic version)
        # (You can improve this by parsing address_components)
        normalized = dict(addr)
        return True, "OK", normalized

    except requests.exceptions.HTTPError as e:
        # resp might exist; data might not. Keep it safe.
        return False, f"HTTP error calling Google: {e}", None
    except requests.exceptions.RequestException as e:
        return False, f"Network error calling Google: {e}", None
    except ValueError as e:
        # JSON decoding error
        return False, f"Could not parse Google response JSON: {e}", None
    except Exception as e:
        return False, f"Unexpected error in validate_address_google: {e}", None
    
def looks_like_insurance_id(s:str) -> bool:
    return bool(re.match(r'^[A-Z0-9]{8,12}$', s.strip()))

