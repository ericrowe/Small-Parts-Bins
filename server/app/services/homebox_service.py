"""Homebox REST API v1 Integration Service.

Communicates exclusively through Homebox's official HTTP REST API (/api/v1) on
Node 02 (http://tasker-pi.local:7745/api/v1) so that all locations, items, tags,
custom fields, asset IDs, search indexes, and photo thumbnails are managed natively
by Homebox without touching Homebox's underlying SQLite database file directly.
"""

from __future__ import annotations

import json
import logging
import os
import re
import socket
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

DEFAULT_HOMEBOX_BASE_URL = "http://tasker-pi.local:7745"

# Optional custom httpx transport (used for hermetic unit testing of the REST client)
_custom_transport: Optional[httpx.BaseTransport] = None
_cached_token: Optional[str] = None


def set_homebox_mock_transport(transport: Optional[httpx.BaseTransport]) -> None:
    """Configure a custom httpx transport (for hermetic unit tests) or reset to None for live HTTP."""
    global _custom_transport, _cached_token
    _custom_transport = transport
    _cached_token = None


def _get_auth_cache_path() -> str:
    """Return local path where the Homebox API Bearer token is cached."""
    custom_path = os.environ.get("HOMEBOX_AUTH_FILE")
    if custom_path:
        return custom_path
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
    )
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "homebox_auth.json")


def _resolve_internal_api_base(public_base_url: str) -> str:
    """
    When running on tasker-pi alongside Homebox (:7745), route backend REST API calls over
    loopback (127.0.0.1:7745) to avoid Avahi mDNS lookup latency/timeouts while preserving
    the public `http://tasker-pi.local:7745` URL for browser-facing links.
    """
    explicit_internal = os.environ.get("HOMEBOX_INTERNAL_BASE_URL")
    if explicit_internal:
        return explicit_internal.rstrip("/")
    try:
        host = socket.gethostname().strip().lower()
        if host.startswith("tasker-pi") and "tasker-pi.local" in public_base_url.lower():
            return re.sub(r"(?i)//tasker-pi\.local\b", "//127.0.0.1", public_base_url)
    except Exception:
        pass
    return public_base_url


def resolve_homebox_paths() -> Dict[str, str]:
    """Return Homebox public base URL (for browser links) and fast internal API v1 endpoint URL."""
    base_url = os.environ.get("HOMEBOX_BASE_URL", DEFAULT_HOMEBOX_BASE_URL).rstrip("/")
    try:
        cache_path = _get_auth_cache_path()
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("base_url") and not os.environ.get("HOMEBOX_BASE_URL"):
                    base_url = data["base_url"].rstrip("/")
    except Exception:
        pass
    internal_base = _resolve_internal_api_base(base_url)
    return {
        "base_url": base_url,
        "internal_base_url": internal_base,
        "api_url": f"{internal_base}/api/v1",
    }


def _normalize_bearer_token(raw_token: str) -> str:
    """Ensure token is formatted cleanly without duplicate 'Bearer ' prefixes."""
    tok = (raw_token or "").strip()
    if tok.lower().startswith("bearer "):
        tok = tok[7:].strip()
    return tok


def _load_saved_token() -> Optional[str]:
    """Load Bearer token from environment or local auth cache file."""
    global _cached_token
    env_tok = os.environ.get("HOMEBOX_API_TOKEN")
    if env_tok:
        return _normalize_bearer_token(env_tok)
    if _cached_token:
        return _cached_token
    cache_path = _get_auth_cache_path()
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                tok = _normalize_bearer_token(data.get("token", ""))
                if tok:
                    _cached_token = tok
                    return tok
        except Exception:
            pass
    return None


def _save_token(token: str, base_url: str, username: str = "") -> None:
    """Persist Bearer token to local auth cache file with 0600 permissions."""
    global _cached_token
    clean_tok = _normalize_bearer_token(token)
    _cached_token = clean_tok
    cache_path = _get_auth_cache_path()
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "token": clean_tok,
                    "base_url": base_url.rstrip("/"),
                    "username": username,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                f,
            )
        os.chmod(cache_path, 0o600)
    except Exception as e:
        logger.warning("Could not persist Homebox auth token cache: %s", e)


def _build_client(token: Optional[str] = None, timeout: float = 15.0) -> httpx.Client:
    """Create an httpx.Client configured with Bearer auth and optional test transport."""
    headers: Dict[str, str] = {"Accept": "application/json"}
    tok = token or _load_saved_token()
    if tok:
        headers["Authorization"] = f"Bearer {_normalize_bearer_token(tok)}"
    return httpx.Client(headers=headers, timeout=timeout, transport=_custom_transport)


def login_to_homebox(
    username: str,
    password: str,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Authenticate against Homebox POST /api/v1/users/login and cache the Bearer token."""
    paths = resolve_homebox_paths()
    target_base = (base_url or paths["base_url"]).rstrip("/")
    login_url = f"{target_base}/api/v1/users/login"

    with _build_client(token=None) as client:
        resp = client.post(
            login_url,
            json={
                "username": username.strip(),
                "password": password,
                "staySignedIn": True,
            },
        )
        if resp.status_code != 200:
            raise ValueError(f"Homebox login failed (HTTP {resp.status_code}): {resp.text}")
        data = resp.json()
        raw_tok = data.get("token") or data.get("access_token") or ""
        if not raw_tok:
            raise ValueError("Homebox login succeeded but did not return an authentication token.")

        _save_token(raw_tok, target_base, username=username.strip())
        return {
            "status": "authenticated",
            "base_url": target_base,
            "username": username.strip(),
            "expires_at": data.get("expiresAt"),
        }


def _ensure_authenticated_token(base_url: str) -> Optional[str]:
    """Return cached token or auto-login if HOMEBOX_USERNAME and HOMEBOX_PASSWORD are set."""
    tok = _load_saved_token()
    if tok:
        return tok
    env_user = os.environ.get("HOMEBOX_USERNAME")
    env_pass = os.environ.get("HOMEBOX_PASSWORD")
    if env_user and env_pass:
        login_to_homebox(env_user, env_pass, base_url=base_url)
        return _load_saved_token()
    return None


def get_homebox_connection_status() -> Dict[str, Any]:
    """Check whether we have a valid Homebox API session and can reach /api/v1/entities (or /api/v1/locations)."""
    paths = resolve_homebox_paths()
    base_url = paths["base_url"]
    tok = _ensure_authenticated_token(base_url)
    if not tok and _custom_transport is None:
        return {
            "authenticated": False,
            "base_url": base_url,
            "message": "Not signed in to Homebox API yet. Enter your Homebox login in the connection bar.",
        }
    try:
        with _build_client(token=tok, timeout=5.0) as client:
            resp = client.get(f"{base_url}/api/v1/entities", params={"isLocation": "true", "pageSize": 5})
            if resp.status_code == 404:
                resp = client.get(f"{base_url}/api/v1/locations")
            if resp.status_code == 200:
                return {
                    "authenticated": True,
                    "base_url": base_url,
                    "message": "Connected to Homebox REST API v1",
                }
            return {
                "authenticated": False,
                "base_url": base_url,
                "message": f"Homebox API returned HTTP {resp.status_code}. Please sign in again.",
            }
    except Exception as e:
        return {
            "authenticated": False,
            "base_url": base_url,
            "message": f"Homebox API unreachable at {base_url}: {e}",
        }


def _flatten_locations(loc_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten a list or tree of Homebox location/entity objects."""
    flat: List[Dict[str, Any]] = []
    for node in loc_nodes:
        if not isinstance(node, dict):
            continue
        flat.append(node)
        children = node.get("children")
        if isinstance(children, list) and children:
            flat.extend(_flatten_locations(children))
    return flat


def _extract_entity_list(data: Any) -> List[Dict[str, Any]]:
    """Extract list of entity objects from Homebox API response (list or paginated dict)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "entities", "entityTypes", "locations", "data"):
            val = data.get(key)
            if isinstance(val, list):
                return val
    return []


def _get_entity_type_ids(client: httpx.Client, api_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve Homebox v0.26+/v0.27+ entityTypeId for Location (`isLocation: true`) and Item (`isLocation: false`).
    Returns `(None, None)` if talking to a pre-v0.26 Homebox instance where `/api/v1/entity-types` returns 404.
    """
    resp = client.get(f"{api_url}/entity-types")
    if resp.status_code == 404:
        return None, None
    if resp.status_code == 401:
        raise PermissionError("Homebox API authentication required (HTTP 401). Please log in to Homebox first.")
    resp.raise_for_status()

    types_list = _extract_entity_list(resp.json())
    location_type_id: Optional[str] = None
    item_type_id: Optional[str] = None

    # Prefer canonical "Location" and "Item" entity types if present
    for et in types_list:
        if not isinstance(et, dict):
            continue
        et_id = et.get("id")
        et_name = (et.get("name") or "").strip().lower()
        is_loc = bool(et.get("isLocation"))
        if is_loc:
            if location_type_id is None or et_name in ("location", "bin", "box", "container"):
                location_type_id = et_id
        else:
            if item_type_id is None or et_name in ("item", "hardware", "fastener", "part"):
                item_type_id = et_id

    if not location_type_id:
        create_loc_type = client.post(
            f"{api_url}/entity-types",
            json={"name": "Location", "isLocation": True},
        )
        if create_loc_type.status_code in (200, 201):
            location_type_id = create_loc_type.json().get("id")

    if not item_type_id:
        create_item_type = client.post(
            f"{api_url}/entity-types",
            json={"name": "Item", "isLocation": False},
        )
        if create_item_type.status_code in (200, 201):
            item_type_id = create_item_type.json().get("id")

    return location_type_id, item_type_id


def _fetch_all_locations(client: httpx.Client, api_url: str) -> List[Dict[str, Any]]:
    """Fetch all locations from GET /api/v1/entities?isLocation=true (with fallback to /api/v1/locations)."""
    resp = client.get(f"{api_url}/entities", params={"isLocation": "true", "pageSize": 500})
    if resp.status_code == 404:
        resp = client.get(f"{api_url}/locations")
    if resp.status_code == 401:
        raise PermissionError("Homebox API authentication required (HTTP 401). Please log in to Homebox first.")
    resp.raise_for_status()
    raw_list = _extract_entity_list(resp.json())
    return _flatten_locations(raw_list)


def _compute_next_bin_from_locations(locations: List[Dict[str, Any]]) -> str:
    """Compute next sequential BIN-XXX identifier from an already-fetched locations list."""
    max_num = 0
    for loc in locations:
        name = (loc.get("name") or "").strip()
        m = re.match(r"^BIN-(\d+)", name, flags=re.IGNORECASE)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"BIN-{max_num + 1:03d}"


def get_next_sequential_bin_name(base_url: Optional[str] = None) -> str:
    """Query Homebox GET /api/v1/entities?isLocation=true for existing BIN-XXX locations and return the next sequential bin ID."""
    paths = resolve_homebox_paths()
    target_base = (base_url or paths["base_url"]).rstrip("/")
    internal_base = _resolve_internal_api_base(target_base)
    api_url = f"{internal_base}/api/v1"
    tok = _ensure_authenticated_token(target_base)

    if not tok and _custom_transport is None:
        return "BIN-001"

    try:
        with _build_client(token=tok, timeout=8.0) as client:
            locations = _fetch_all_locations(client, api_url)
            return _compute_next_bin_from_locations(locations)
    except Exception as e:
        logger.warning("Fallback BIN-001 (could not query Homebox locations: %s)", e)
        return "BIN-001"


def _get_or_create_tag_api(
    client: httpx.Client,
    api_url: str,
    existing_tags: List[Dict[str, Any]],
    tag_name: str,
    color: str = "#0284c7",
) -> str:
    """Find or create a tag via GET/POST /api/v1/tags."""
    for t in existing_tags:
        if (t.get("name") or "").strip().lower() == tag_name.strip().lower():
            return t["id"]

    resp = client.post(
        f"{api_url}/tags",
        json={
            "name": tag_name.strip(),
            "description": f"Auto-created by Parts Ingestor ({tag_name})",
            "color": color,
        },
    )
    resp.raise_for_status()
    created = resp.json()
    existing_tags.append(created)
    return created["id"]


def _get_location_parent_id(loc: Dict[str, Any]) -> Optional[str]:
    """Extract parentId from a Homebox location/entity object."""
    parent_obj = loc.get("parent")
    if isinstance(parent_obj, dict) and parent_obj.get("id"):
        return parent_obj["id"]
    return loc.get("parentId")


def _ensure_location_node_api(
    client: httpx.Client,
    api_url: str,
    locations: List[Dict[str, Any]],
    name: str,
    description: str,
    parent_id: Optional[str],
    location_type_id: Optional[str] = None,
) -> str:
    """Find or create a location node by name and ensure its parentId matches `parent_id`."""
    target_lower = name.strip().lower()
    existing_loc: Optional[Dict[str, Any]] = None
    for loc in locations:
        if (loc.get("name") or "").strip().lower() == target_lower:
            existing_loc = loc
            break

    if existing_loc:
        loc_id = existing_loc["id"]
        current_parent = _get_location_parent_id(existing_loc)
        if parent_id is not None and current_parent != parent_id:
            # Reparent existing location node (e.g. moving Gridfinity Cartridges from Garage -> Barn > Tool Chest A)
            endpoint = f"{api_url}/entities/{loc_id}" if location_type_id else f"{api_url}/locations/{loc_id}"
            update_body = dict(existing_loc)
            update_body["parentId"] = parent_id
            if location_type_id:
                update_body["entityTypeId"] = location_type_id
            put_resp = client.put(endpoint, json=update_body)
            if put_resp.status_code == 200:
                existing_loc.update(put_resp.json())
            existing_loc["parentId"] = parent_id
        return loc_id

    create_payload: Dict[str, Any] = {
        "name": name.strip(),
        "description": description,
        "parentId": parent_id,
    }
    if location_type_id:
        create_payload["entityTypeId"] = location_type_id
        resp = client.post(f"{api_url}/entities", json=create_payload)
    else:
        resp = client.post(f"{api_url}/locations", json=create_payload)
    resp.raise_for_status()
    created = resp.json()
    locations.append(created)
    return created["id"]


def _get_or_create_cartridges_root_api(
    client: httpx.Client,
    api_url: str,
    locations: List[Dict[str, Any]],
    location_type_id: Optional[str] = None,
) -> str:
    """Ensure the 'Barn > Tool Chest A > Gridfinity Cartridges' location hierarchy exists in Homebox."""
    barn_id = _ensure_location_node_api(
        client=client,
        api_url=api_url,
        locations=locations,
        name="Barn",
        description="Barn Workshop",
        parent_id=None,
        location_type_id=location_type_id,
    )
    tool_chest_id = _ensure_location_node_api(
        client=client,
        api_url=api_url,
        locations=locations,
        name="Tool Chest A",
        description="Tool Chest A in Barn",
        parent_id=barn_id,
        location_type_id=location_type_id,
    )
    cartridges_root_id = _ensure_location_node_api(
        client=client,
        api_url=api_url,
        locations=locations,
        name="Gridfinity Cartridges",
        description="Modular 40x80 mm glass-window hardware cartridges (Barn > Tool Chest A > Gridfinity Cartridges).",
        parent_id=tool_chest_id,
        location_type_id=location_type_id,
    )
    return cartridges_root_id


def commit_cartridge_to_homebox(
    payload: Dict[str, Any],
    photo_bytes: Optional[bytes] = None,
    photo_filename: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Commit a cataloged cartridge (sequential bin location + 1..N part items) via Homebox's REST API (/api/v1)."""
    paths = resolve_homebox_paths()
    target_base = (base_url or paths["base_url"]).rstrip("/")
    internal_base = _resolve_internal_api_base(target_base)
    api_url = f"{internal_base}/api/v1"
    tok = _ensure_authenticated_token(target_base)

    if not tok and _custom_transport is None:
        raise ValueError(
            "Not authenticated with Homebox API. Please enter your Homebox credentials in the 'Homebox API Connection' panel first."
        )

    groups = payload.get("groups") or []
    if not groups:
        raise ValueError("At least one hardware group/item is required to commit a cartridge.")

    cartridge_label = (payload.get("cartridge_label") or "").strip()

    with _build_client(token=tok, timeout=20.0) as client:
        location_type_id, item_type_id = _get_entity_type_ids(client, api_url)
        use_entities_api = location_type_id is not None or item_type_id is not None
        locations = _fetch_all_locations(client, api_url)

        requested_bin = (payload.get("bin_id") or "").strip().upper()
        if not requested_bin or not re.match(r"^BIN-\d+", requested_bin):
            max_num = 0
            for loc in locations:
                m = re.match(r"^BIN-(\d+)", (loc.get("name") or "").strip(), flags=re.IGNORECASE)
                if m:
                    max_num = max(max_num, int(m.group(1)))
            requested_bin = f"BIN-{max_num + 1:03d}"

        parent_loc_id = _get_or_create_cartridges_root_api(client, api_url, locations, location_type_id=location_type_id)
        bin_display_name = f"{requested_bin} ({cartridge_label})" if cartridge_label else requested_bin

        # Check if BIN-XXX location already exists
        existing_bin_loc: Optional[Dict[str, Any]] = None
        for loc in locations:
            lname = (loc.get("name") or "").strip().upper()
            if lname == requested_bin or lname.startswith(f"{requested_bin} "):
                existing_bin_loc = loc
                break

        if existing_bin_loc:
            bin_entity_id = existing_bin_loc["id"]
        else:
            loc_payload: Dict[str, Any] = {
                "name": bin_display_name,
                "description": f"Sequential Cartridge Bin {requested_bin}"
                + (f" — {cartridge_label}" if cartridge_label else ""),
                "parentId": parent_loc_id,
            }
            if use_entities_api:
                if location_type_id:
                    loc_payload["entityTypeId"] = location_type_id
                loc_resp = client.post(f"{api_url}/entities", json=loc_payload)
            else:
                loc_resp = client.post(f"{api_url}/locations", json=loc_payload)
            loc_resp.raise_for_status()
            created_loc = loc_resp.json()
            bin_entity_id = created_loc["id"]
            locations.append(created_loc)

        # Fetch existing tags via GET /api/v1/tags
        tags_resp = client.get(f"{api_url}/tags")
        tags_resp.raise_for_status()
        existing_tags = _extract_entity_list(tags_resp.json())

        fastener_tag_id = _get_or_create_tag_api(client, api_url, existing_tags, "Fasteners", "#0284c7")
        cartridge_tag_id = _get_or_create_tag_api(client, api_url, existing_tags, "Cartridge-Ingest", "#10b981")

        head_display_map = {
            "shcs": "Socket Head Cap Screw (SHCS)",
            "socket": "Socket Head Cap Screw (SHCS)",
            "bhcs": "Button Head Cap Screw (BHCS)",
            "button": "Button Head Cap Screw (BHCS)",
            "fhcs": "Flat / Countersunk Head Screw (FHCS)",
            "flat": "Flat / Countersunk Head Screw (FHCS)",
            "hex": "Hex Head Bolt",
            "pan": "Pan Head Screw",
            "truss": "Truss Head Screw",
            "round": "Round Head Screw",
            "nut": "Hex Nut",
            "nyloc": "Nyloc Lock Nut",
            "flange_nut": "Flange Hex Nut",
            "square_nut": "Square Nut",
            "wing_nut": "Wing Nut",
            "tnut": "T-Nut",
            "tnut_pre": "Pre-Insert T-Nut",
            "tnut_post": "Post-Insert T-Nut",
            "washer": "Flat Washer",
            "fender_washer": "Fender Washer",
            "split_washer": "Split Lock Washer",
            "insert": "Heat-Set Insert",
        }

        created_items: List[Dict[str, Any]] = []

        for grp in groups:
            size = (grp.get("size") or "").strip()
            length = (grp.get("length") or "").strip()
            if length and not any(u in length.lower() for u in ("mm", "in", "\"")):
                if size.upper().startswith("M"):
                    length = f"{length} mm"
            pitch = (grp.get("pitch") or "").strip()
            head_code = (grp.get("head") or "shcs").strip().lower()
            drive_code = (grp.get("drive") or "hex").strip().lower()
            comp_type = (grp.get("comp_type") or ("nut" if head_code in ("nut", "nyloc", "flange_nut", "square_nut", "wing_nut", "tnut", "tnut_pre", "tnut_post") else "washer" if head_code in ("washer", "fender_washer", "split_washer") else "insert" if head_code == "insert" else "bolt")).strip().lower()
            finish = (grp.get("finish") or grp.get("material") or "Steel").strip()
            finish_key = (grp.get("finish_key") or "").strip().lower()
            qty = max(1, int(grp.get("quantity") if grp.get("quantity") is not None else (grp.get("count") or 1)))
            tool_key = (grp.get("tool_key") or "").strip()
            tap_drill = (grp.get("tap_drill") or "").strip()
            clearance_drill = (grp.get("clearance_drill") or "").strip()
            grp_notes = (grp.get("notes") or "").strip()

            head_label = head_display_map.get(head_code, head_code.upper())

            dim_part = f"{size} × {length}".strip(" ×") if (size and length) else (size or length or "Hardware Part")
            item_name = (grp.get("name") or "").strip()
            if not item_name:
                item_name = f"{dim_part} {head_label} ({finish})"

            model_parts = [p for p in (size, length.replace(" ", ""), head_code.upper(), (finish_key.upper() or finish[:3].upper())) if p]
            model_code = "-".join(model_parts)
            description = f"{dim_part} {head_label} | Finish: {finish}" + (f" | Pitch: {pitch}" if pitch else "")

            tag_ids = {fastener_tag_id, cartridge_tag_id}
            if size.upper().startswith("M"):
                tag_ids.add(_get_or_create_tag_api(client, api_url, existing_tags, "Metric", "#0077CC"))
            elif size:
                tag_ids.add(_get_or_create_tag_api(client, api_url, existing_tags, "Imperial", "#E65100"))

            if "black" in finish.lower() or finish_key == "black":
                tag_ids.add(_get_or_create_tag_api(client, api_url, existing_tags, "Black Oxide", "#334155"))
            elif "silver" in finish.lower() or "stainless" in finish.lower() or finish_key == "silver":
                tag_ids.add(_get_or_create_tag_api(client, api_url, existing_tags, "Stainless / Silver", "#94a3b8"))

            len_field_label = "Outer Diameter (OD)" if comp_type == "washer" else "Length"
            custom_fields_pairs = [
                ("Temporary Bin", requested_bin),
                ("Thread Size", size),
                (len_field_label, length),
                ("Pitch", pitch),
                ("Head Style", head_label),
                ("Drive Type", drive_code.upper()),
                ("Component Type", comp_type),
                ("Finish / Color", finish),
                ("Tool / Hex Key", tool_key),
                ("Tap Drill", tap_drill),
                ("Clearance Drill", clearance_drill),
            ]
            fields_payload = [
                {
                    "name": f_name,
                    "type": "text",
                    "textValue": str(f_val),
                    "numberValue": 0,
                    "booleanValue": False,
                }
                for f_name, f_val in custom_fields_pairs
                if f_val
            ]

            item_notes = (
                grp_notes
                or f"Stored in {requested_bin}. Separate finish/variant ({finish}) inside single cartridge bin."
            )

            # 1. Create Item via POST /api/v1/entities (or legacy /api/v1/items)
            if use_entities_api:
                create_item_body: Dict[str, Any] = {
                    "name": item_name,
                    "description": description,
                    "quantity": qty,
                    "parentId": bin_entity_id,
                    "tagIds": list(tag_ids),
                    "notes": item_notes,
                    "serialNumber": requested_bin,
                    "modelNumber": model_code,
                    "manufacturer": finish,
                    "fields": fields_payload,
                }
                if item_type_id:
                    create_item_body["entityTypeId"] = item_type_id
                create_resp = client.post(f"{api_url}/entities", json=create_item_body)
            else:
                create_resp = client.post(
                    f"{api_url}/items",
                    json={
                        "name": item_name,
                        "description": description,
                        "quantity": qty,
                        "locationId": bin_entity_id,
                        "tagIds": list(tag_ids),
                    },
                )
            create_resp.raise_for_status()
            item_obj = create_resp.json()
            item_id = item_obj["id"]

            # 2. Enrich Item with custom fields, notes, modelNumber, manufacturer via PUT
            entity_endpoint = f"{api_url}/entities/{item_id}" if use_entities_api else f"{api_url}/items/{item_id}"
            detail_resp = client.get(entity_endpoint)
            detail_obj = detail_resp.json() if detail_resp.status_code == 200 else dict(item_obj)
            detail_obj.update(
                {
                    "id": item_id,
                    "name": item_name,
                    "description": description,
                    "quantity": qty,
                    "tagIds": list(tag_ids),
                    "notes": item_notes,
                    "serialNumber": requested_bin,
                    "modelNumber": model_code,
                    "manufacturer": finish,
                    "fields": fields_payload,
                }
            )
            if use_entities_api:
                detail_obj["parentId"] = bin_entity_id
                if item_type_id:
                    detail_obj["entityTypeId"] = item_type_id
            else:
                detail_obj["locationId"] = bin_entity_id

            put_resp = client.put(entity_endpoint, json=detail_obj)
            if put_resp.status_code == 200:
                item_obj = put_resp.json()

            # 3. Upload photo attachment via POST /api/v1/entities/{id}/attachments (or /items/{id}/attachments)
            if photo_bytes:
                fname = photo_filename or f"{requested_bin.lower()}_cartridge.jpg"
                client.post(
                    f"{entity_endpoint}/attachments",
                    files={"file": (fname, photo_bytes, "image/jpeg")},
                    data={"type": "photo", "name": fname, "primary": "true"},
                )

            created_items.append(
                {
                    "id": item_id,
                    "asset_id": item_obj.get("assetId", 0),
                    "name": item_name,
                    "size": size,
                    "length": length,
                    "pitch": pitch,
                    "head": head_code,
                    "head_label": head_label,
                    "finish": finish,
                    "quantity": qty,
                    "bin_id": requested_bin,
                    "homebox_url": f"{target_base}/item/{item_id}",
                }
            )

    next_bin_after = get_next_sequential_bin_name(target_base)
    homebox_bin_url = f"{target_base}/location/{bin_entity_id}"
    register_qr_forwarding_entry(
        bin_code=requested_bin,
        target_url=homebox_bin_url,
        label=bin_display_name,
        location_id=bin_entity_id,
    )
    return {
        "status": "success",
        "bin_id": requested_bin,
        "bin_entity_id": bin_entity_id,
        "bin_display_name": bin_display_name,
        "homebox_bin_url": homebox_bin_url,
        "created_items": created_items,
        "next_bin_id": next_bin_after,
    }


def _get_qr_forwarding_file_path() -> str:
    """Return local JSON path storing the 4-digit QR forwarding lookup table."""
    custom_path = os.environ.get("QR_FORWARDING_FILE")
    if custom_path:
        return custom_path
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
    )
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "qr_forwarding.json")


def _normalize_four_digit_code(raw_code: str) -> str:
    """Normalize '0001', '1', 'BIN-001', or 'BIN-0001' into a 4-digit string ('0001')."""
    m = re.search(r"(\d+)", str(raw_code or ""))
    if m:
        return f"{int(m.group(1)):04d}"
    return str(raw_code or "").strip().upper()


def _normalize_homebox_web_url(url: str) -> str:
    """Ensure Homebox frontend entity routes use singular /location/{id} and /item/{id}."""
    cleaned = (url or "").strip()
    cleaned = re.sub(r"/locations/([^/?#]+)", r"/location/\1", cleaned)
    cleaned = re.sub(r"/items/([^/?#]+)", r"/item/\1", cleaned)
    return cleaned


def register_qr_forwarding_entry(
    bin_code: str,
    target_url: str,
    label: str = "",
    location_id: str = "",
    manual_override: bool = False,
    preserve_existing: bool = False,
) -> Dict[str, Any]:
    """
    Register or update a 4-digit QR code forwarding target in qr_forwarding.json.
    When preserve_existing=True (used by background Homebox syncs), any existing entry
    for `code_4d` is preserved so manual edits in qr_forwarding.json or UI overrides are never overwritten.
    """
    code_4d = _normalize_four_digit_code(bin_code)
    norm_target = _normalize_homebox_web_url(target_url)
    path = _get_qr_forwarding_file_path()
    entries: Dict[str, Any] = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    entries = loaded
        except Exception:
            entries = {}

    existing = entries.get(code_4d)
    if preserve_existing and isinstance(existing, dict) and existing.get("target_url"):
        norm_existing = _normalize_homebox_web_url(existing["target_url"])
        dirty_existing = False
        if norm_existing != existing["target_url"]:
            existing["target_url"] = norm_existing
            dirty_existing = True
        if label and not existing.get("manual_override") and existing.get("label") != label:
            existing["label"] = label
            dirty_existing = True
        if "printed" not in existing:
            existing["printed"] = False
            dirty_existing = True
        if dirty_existing:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(entries, f, indent=2)
            except Exception:
                pass
        return existing

    prev_printed = bool(existing.get("printed", False)) if isinstance(existing, dict) else False
    prev_printed_at = existing.get("printed_at", "") if isinstance(existing, dict) else ""
    entry = {
        "code": code_4d,
        "target_url": norm_target,
        "label": label or (existing.get("label", "") if isinstance(existing, dict) else ""),
        "location_id": location_id or (existing.get("location_id", "") if isinstance(existing, dict) else ""),
        "manual_override": bool(manual_override),
        "printed": prev_printed,
        "printed_at": prev_printed_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    entries[code_4d] = entry
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except Exception as e:
        logger.warning("Could not save QR forwarding entry: %s", e)
    return entry


def set_bins_printed_status(bin_codes: List[str], printed: bool = True) -> List[Dict[str, Any]]:
    """Mark one or more 4-digit bin codes as printed (or unprinted) in qr_forwarding.json."""
    path = _get_qr_forwarding_file_path()
    entries: Dict[str, Any] = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    entries = loaded
        except Exception:
            entries = {}

    now_iso = datetime.now(timezone.utc).isoformat()
    paths = resolve_homebox_paths()
    default_target = f"{paths['base_url']}/location"
    updated_entries: List[Dict[str, Any]] = []

    for raw in bin_codes:
        code_4d = _normalize_four_digit_code(raw)
        if not code_4d:
            continue
        item = entries.get(code_4d)
        if not isinstance(item, dict):
            item = {
                "code": code_4d,
                "target_url": default_target,
                "label": f"BIN-{code_4d}",
                "location_id": "",
                "manual_override": False,
                "updated_at": now_iso,
            }
        item["printed"] = bool(printed)
        item["printed_at"] = now_iso if printed else ""
        entries[code_4d] = item
        updated_entries.append(item)

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except Exception as e:
        logger.warning("Could not persist bin printed status: %s", e)

    return updated_entries


def list_qr_forwarding_entries() -> List[Dict[str, Any]]:
    """Return all 4-digit QR forwarding entries from qr_forwarding.json, sorted by 4-digit code."""
    path = _get_qr_forwarding_file_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            entries = json.load(f)
        if not isinstance(entries, dict):
            return []
        result: List[Dict[str, Any]] = []
        dirty = False
        for code_key in sorted(entries.keys()):
            item = entries.get(code_key)
            if not isinstance(item, dict):
                continue
            raw_url = item.get("target_url") or ""
            norm_url = _normalize_homebox_web_url(raw_url)
            if norm_url != raw_url:
                item["target_url"] = norm_url
                dirty = True
            result.append(
                {
                    "code": item.get("code") or _normalize_four_digit_code(code_key),
                    "target_url": norm_url,
                    "label": item.get("label") or "",
                    "location_id": item.get("location_id") or "",
                    "manual_override": bool(item.get("manual_override", False)),
                    "printed": bool(item.get("printed", False)),
                    "printed_at": item.get("printed_at") or "",
                    "updated_at": item.get("updated_at") or "",
                }
            )
        if dirty:
            with open(path, "w", encoding="utf-8") as fw:
                json.dump(entries, fw, indent=2)
        return result
    except Exception:
        return []


def delete_qr_forwarding_entry(bin_code: str) -> bool:
    """Delete a 4-digit QR forwarding entry from qr_forwarding.json so it can be re-synced from Homebox or removed."""
    code_4d = _normalize_four_digit_code(bin_code)
    path = _get_qr_forwarding_file_path()
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            entries = json.load(f)
        if isinstance(entries, dict) and code_4d in entries:
            del entries[code_4d]
            with open(path, "w", encoding="utf-8") as fw:
                json.dump(entries, fw, indent=2)
            return True
    except Exception:
        pass
    return False


def has_qr_forwarding_entry(bin_code: str) -> bool:
    """Return True if a 4-digit QR bin code is explicitly registered in qr_forwarding.json."""
    code_4d = _normalize_four_digit_code(bin_code)
    path = _get_qr_forwarding_file_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)
            if isinstance(entries, dict) and code_4d in entries:
                return bool((entries[code_4d] or {}).get("target_url"))
        except Exception:
            pass
    return False


def resolve_qr_forwarding_target(bin_code: str, base_url: Optional[str] = None) -> str:
    """
    Resolve a 4-digit QR bin code (e.g. '0001') into its target redirect URL:
      1. Look up in local qr_forwarding.json table (normalizing /locations/{id} -> /location/{id}).
      2. If not cached locally, query Homebox /api/v1/entities?isLocation=true for matching BIN-XXXX / BIN-XXX.
      3. Fall back to Homebox locations overview.
    """
    code_4d = _normalize_four_digit_code(bin_code)
    path = _get_qr_forwarding_file_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)
            if isinstance(entries, dict) and code_4d in entries:
                target = (entries[code_4d] or {}).get("target_url")
                if target:
                    norm_target = _normalize_homebox_web_url(target)
                    if norm_target != target:
                        entries[code_4d]["target_url"] = norm_target
                        with open(path, "w", encoding="utf-8") as fw:
                            json.dump(entries, fw, indent=2)
                    return norm_target
        except Exception:
            pass

    paths = resolve_homebox_paths()
    target_base = (base_url or paths["base_url"]).rstrip("/")
    internal_base = _resolve_internal_api_base(target_base)
    api_url = f"{internal_base}/api/v1"
    tok = _ensure_authenticated_token(target_base)

    try:
        num_val = int(code_4d) if code_4d.isdigit() else None
    except ValueError:
        num_val = None

    if (tok or _custom_transport is not None) and num_val is not None:
        try:
            with _build_client(token=tok, timeout=6.0) as client:
                locations = _fetch_all_locations(client, api_url)
                for loc in locations:
                    name = (loc.get("name") or "").strip()
                    m = re.match(r"^(?:BIN-)?(\d+)\b", name, flags=re.IGNORECASE)
                    if m and int(m.group(1)) == num_val:
                        loc_url = f"{target_base}/location/{loc['id']}"
                        register_qr_forwarding_entry(
                            bin_code=code_4d,
                            target_url=loc_url,
                            label=name,
                            location_id=loc["id"],
                        )
                        return loc_url
        except Exception:
            pass

    return f"{target_base}/location"


def _extract_cartridge_specs_from_homebox_bin(
    b_name: str,
    b_desc: str,
    bin_code: str,
    items_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Parse thread size, bare length, category color bar, and finish summary from a Homebox BIN location."""
    bin_4digit = _normalize_four_digit_code(bin_code)
    combined_header = f"{b_name} {b_desc}".strip()
    first_item_name = items_list[0].get("name", "") if items_list else ""
    first_item_desc = items_list[0].get("description", "") if items_list else ""
    all_items_blob = " ".join(
        f"{it.get('name', '')} {it.get('description', '')}" for it in items_list
    ).strip()
    search_blob = f"{combined_header} {all_items_blob}" if all_items_blob else f"{combined_header} {first_item_name} {first_item_desc}"

    size = ""
    length = ""

    # 1. Try metric pattern (including multi-chamber lengths like "M2 × 6, 8, 10" or "M4 × 6"):
    m_metric = re.search(
        r"\b(M\d+(?:\.\d+)?)\s*(?:[×xX*\s\-]+(\d+(?:\.\d+)?(?:\s*(?:mm)?\s*[,/]\s*\d+(?:\.\d+)?)*)\s*(?:mm)?)?\b",
        search_blob,
        flags=re.IGNORECASE,
    )
    if m_metric:
        size = m_metric.group(1).upper()
        if m_metric.group(2):
            length = re.sub(r"(?i)\s*mm\b", "", m_metric.group(2)).strip()

    # 2. Try imperial pattern if not metric: e.g. "#6-32 × 1/2", "1/4-20 x 3/4"
    if not size:
        m_imp = re.search(
            r"(#[0-9]+-[0-9]+|\d+/\d+-[0-9]+)\s*(?:[×xX*]\s*([0-9/\-\.\"]+))?",
            search_blob,
            flags=re.IGNORECASE,
        )
        if m_imp:
            size = m_imp.group(1)
            if m_imp.group(2):
                length = m_imp.group(2).rstrip('"')

    # 3. Try parenthesized label in location name if still empty: e.g. "BIN-001 (M4)"
    if not size:
        m_paren = re.search(r"\(([^)]+)\)", b_name)
        if m_paren:
            inner = m_paren.group(1).strip()
            parts = re.split(r"\s*[×xX]\s*", inner, maxsplit=1)
            size = parts[0].strip()
            if len(parts) > 1:
                length = re.sub(r"\s*mm$", "", parts[1].strip(), flags=re.IGNORECASE)

    # Determine category, component type & top bar color (check nuts/washers/t-nuts BEFORE 'insert' so 'Pre-Insert T-Nut' is a nut, not a heat-set insert!)
    lower_blob = search_blob.lower()
    comp_type = "bolt"
    head_detected = "shcs"
    if any(k in lower_blob for k in ("washer", "fender", "nut", "nyloc", "t-nut", "tnut")):
        category_id = "nuts_washers"
        category_name = "Nuts & Washers"
        accent_color = "#E65100" if (size and not size.upper().startswith("M")) else "#0077CC"
        if "washer" in lower_blob or "fender" in lower_blob:
            comp_type = "washer"
            head_detected = "fender_washer" if "fender" in lower_blob else "split_washer" if "split" in lower_blob else "washer"
            # Aggregate all known Outer Diameters (ODs) across items in this bin (omit any washer whose OD is unknown)
            known_numeric_ods: Dict[float, str] = {}
            known_other_ods: List[str] = []
            sources_to_scan = [
                f"{it.get('name', '')} {it.get('description', '')}" for it in items_list
            ] if items_list else [combined_header]
            for src_txt in sources_to_scan:
                for m_od in re.finditer(
                    r"\b(?:M\d+(?:\.\d+)?)\s*[×xX*]\s*(\d+(?:\.\d+)?(?:\s*(?:mm)?\s*[,/]\s*\d+(?:\.\d+)?)*)\s*(?:mm)?\b",
                    src_txt,
                    flags=re.IGNORECASE,
                ):
                    raw_nums = m_od.group(1)
                    for token in re.split(r"[,/]+", raw_nums):
                        tok_clean = re.sub(r"(?i)\s*mm\b", "", token).strip()
                        if not tok_clean:
                            continue
                        try:
                            fval = float(tok_clean)
                            fmt_od = f"{int(fval)}mm" if fval.is_integer() else f"{fval:g}mm"
                            known_numeric_ods[fval] = fmt_od
                        except ValueError:
                            if tok_clean not in known_other_ods:
                                known_other_ods.append(tok_clean)
            if known_numeric_ods or known_other_ods:
                sorted_ods = [known_numeric_ods[k] for k in sorted(known_numeric_ods.keys())] + known_other_ods
                length = ", ".join(sorted_ods)
            else:
                length = ""
        else:
            comp_type = "nut"
            head_detected = (
                "nyloc"
                if "nyloc" in lower_blob
                else "tnut_pre"
                if ("pre-insert" in lower_blob or "pre_insert" in lower_blob)
                else "tnut_post"
                if ("post-insert" in lower_blob or "post_insert" in lower_blob)
                else "tnut_pre"
                if ("t-nut" in lower_blob or "tnut" in lower_blob)
                else "flange_nut"
                if "flange" in lower_blob
                else "square_nut"
                if "square" in lower_blob
                else "nut"
            )
    elif "insert" in lower_blob or "standoff" in lower_blob or "dowel" in lower_blob or "specialty" in lower_blob:
        category_id = "inserts"
        category_name = "Inserts, Standoffs & Specialty"
        accent_color = "#D4A017"
        comp_type = "insert"
        head_detected = "insert"
    elif size and not size.upper().startswith("M"):
        category_id = "imperial"
        category_name = "Imperial Fasteners"
        accent_color = "#E65100"
    else:
        category_id = "metric"
        category_name = "Metric Fasteners"
        accent_color = "#0077CC"

    pitch = ""
    m_pitch = re.search(r"Pitch:\s*([0-9.]+\s*(?:mm|TPI)?)", first_item_desc, flags=re.IGNORECASE)
    if m_pitch:
        pitch = m_pitch.group(1).strip()

    # Optional special detail note (blank by default unless explicitly noted with [Note: ...])
    extra_note = ""
    m_note = re.search(r"\[Note:\s*([^\]]+)\]", b_desc, flags=re.IGNORECASE)
    if m_note:
        extra_note = m_note.group(1).strip()

    # Summarize finishes/heads inside this Homebox bin
    finish_parts: List[str] = []
    for it in items_list:
        q = it.get("quantity", 0)
        fin = it.get("finish") or ""
        nm = it.get("name") or ""
        head_tag = ""
        for code in ("SHCS", "BHCS", "FHCS", "Nyloc", "Nut", "Fender Washer", "Washer", "Hex", "Pan"):
            if code.lower() in nm.lower():
                head_tag = code
                break
        short_fin = "Black" if "black" in (fin + nm).lower() else ("Silver" if any(k in (fin + nm).lower() for k in ("silver", "stainless", "ss")) else fin)
        label_piece = f"{q}× {short_fin} {head_tag}".strip()
        if label_piece:
            finish_parts.append(label_piece)

    return {
        "bin_4digit": bin_4digit,
        "size": size or bin_code,
        "length": length,
        "pitch": pitch,
        "comp_type": comp_type,
        "head": head_detected,
        "category_id": category_id,
        "category_name": category_name,
        "accent_color": accent_color,
        "extra_note": extra_note,
        "finishes_summary": ", ".join(finish_parts) if finish_parts else "Empty / Pre-assigned Bin",
        "qr_short_url": f"HTTP://TASKER-PI.LOCAL:8090/{bin_4digit}",
    }


def list_ingested_bins(base_url: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Return all sequential BIN-XXX locations and their contained hardware items via Homebox REST API."""
    paths = resolve_homebox_paths()
    target_base = (base_url or paths["base_url"]).rstrip("/")
    internal_base = _resolve_internal_api_base(target_base)
    api_url = f"{internal_base}/api/v1"
    tok = _ensure_authenticated_token(target_base)

    if not tok and _custom_transport is None:
        return {
            "homebox_base_url": target_base,
            "homebox_locations_url": target_base,
            "authenticated": False,
            "next_bin_id": "BIN-001",
            "total_bins": 0,
            "bins": [],
        }

    try:
        with _build_client(token=tok, timeout=10.0) as client:
            locations = _fetch_all_locations(client, api_url)
            cartridges_root_id: Optional[str] = None
            for loc in locations:
                if (loc.get("name") or "").strip().lower() == "gridfinity cartridges":
                    cartridges_root_id = loc.get("id")
                    break
            homebox_locations_url = f"{target_base}/location/{cartridges_root_id}" if cartridges_root_id else target_base
            next_bin_id = _compute_next_bin_from_locations(locations)
            bin_locs = [
                loc
                for loc in locations
                if re.match(r"^BIN-\d+", (loc.get("name") or "").strip(), flags=re.IGNORECASE)
            ]
            bin_locs.sort(key=lambda x: (x.get("name") or ""), reverse=True)
            bin_locs = bin_locs[:limit]

            # Fetch items from Homebox (/api/v1/entities in v0.26+/v0.27+, fallback to /api/v1/items)
            items_resp = client.get(f"{api_url}/entities", params={"isLocation": "false", "pageSize": 500})
            if items_resp.status_code == 404:
                items_resp = client.get(f"{api_url}/items", params={"pageSize": 500})
            items_resp.raise_for_status()
            all_items = _extract_entity_list(items_resp.json())

            items_by_loc: Dict[str, List[Dict[str, Any]]] = {}
            for it in all_items:
                parent_obj = it.get("parent") or {}
                loc_obj = it.get("location") or {}
                loc_id = (
                    parent_obj.get("id")
                    or it.get("parentId")
                    or loc_obj.get("id")
                    or it.get("locationId")
                )
                if loc_id:
                    items_by_loc.setdefault(loc_id, []).append(it)

            # Load qr_forwarding.json once for the entire batch rather than on every bin iteration
            fwd_path = _get_qr_forwarding_file_path()
            fwd_entries: Dict[str, Any] = {}
            if os.path.exists(fwd_path):
                try:
                    with open(fwd_path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                        if isinstance(loaded, dict):
                            fwd_entries = loaded
                except Exception:
                    fwd_entries = {}
            fwd_dirty = False
            now_iso = datetime.now(timezone.utc).isoformat()

            bins_out: List[Dict[str, Any]] = []
            for b_loc in bin_locs:
                b_id = b_loc["id"]
                b_name = b_loc.get("name") or ""
                b_desc = b_loc.get("description") or ""
                m = re.match(r"^(BIN-\d+)", b_name.strip(), flags=re.IGNORECASE)
                bin_code = m.group(1).upper() if m else b_name

                loc_items = items_by_loc.get(b_id, [])
                items_list = [
                    {
                        "id": r["id"],
                        "name": r.get("name", ""),
                        "description": r.get("description", ""),
                        "quantity": int(r.get("quantity") or 0),
                        "asset_id": r.get("assetId", 0),
                        "model_number": r.get("modelNumber", ""),
                        "finish": r.get("manufacturer", ""),
                        "homebox_url": f"{target_base}/item/{r['id']}",
                    }
                    for r in loc_items
                ]

                hb_loc_url = f"{target_base}/location/{b_id}"
                specs = _extract_cartridge_specs_from_homebox_bin(
                    b_name=b_name,
                    b_desc=b_desc,
                    bin_code=bin_code,
                    items_list=items_list,
                )
                code_4d = specs["bin_4digit"]
                norm_target = _normalize_homebox_web_url(hb_loc_url)
                existing_fwd = fwd_entries.get(code_4d)
                if isinstance(existing_fwd, dict) and existing_fwd.get("target_url"):
                    norm_existing = _normalize_homebox_web_url(existing_fwd["target_url"])
                    if norm_existing != existing_fwd["target_url"]:
                        existing_fwd["target_url"] = norm_existing
                        fwd_dirty = True
                    if b_name and not existing_fwd.get("manual_override") and existing_fwd.get("label") != b_name:
                        existing_fwd["label"] = b_name
                        fwd_dirty = True
                    if "printed" not in existing_fwd:
                        existing_fwd["printed"] = False
                        fwd_dirty = True
                    fwd_entry = existing_fwd
                else:
                    fwd_entry = {
                        "code": code_4d,
                        "target_url": norm_target,
                        "label": b_name,
                        "location_id": b_id,
                        "manual_override": False,
                        "printed": False,
                        "printed_at": "",
                        "updated_at": now_iso,
                    }
                    fwd_entries[code_4d] = fwd_entry
                    fwd_dirty = True

                bins_out.append(
                    {
                        "id": b_id,
                        "bin_code": bin_code,
                        "bin_4digit": specs["bin_4digit"],
                        "name": b_name,
                        "description": b_desc,
                        "size": specs["size"],
                        "length": specs["length"],
                        "pitch": specs["pitch"],
                        "comp_type": specs.get("comp_type", "bolt"),
                        "head": specs.get("head", "shcs"),
                        "category_id": specs["category_id"],
                        "category_name": specs["category_name"],
                        "accent_color": specs["accent_color"],
                        "extra_note": specs["extra_note"],
                        "finishes_summary": specs["finishes_summary"],
                        "qr_short_url": specs["qr_short_url"],
                        "printed": bool(fwd_entry.get("printed", False)),
                        "printed_at": fwd_entry.get("printed_at", ""),
                        "updated_at": b_loc.get("updatedAt", ""),
                        "homebox_url": hb_loc_url,
                        "item_count": len(items_list),
                        "total_pieces": sum(i["quantity"] for i in items_list),
                        "items": items_list,
                    }
                )

            if fwd_dirty:
                try:
                    os.makedirs(os.path.dirname(fwd_path), exist_ok=True)
                    with open(fwd_path, "w", encoding="utf-8") as fw:
                        json.dump(fwd_entries, fw, indent=2)
                except Exception as e:
                    logger.warning("Could not save batched QR forwarding entries: %s", e)

            return {
                "homebox_base_url": target_base,
                "homebox_locations_url": homebox_locations_url,
                "authenticated": True,
                "next_bin_id": next_bin_id,
                "total_bins": len(bins_out),
                "bins": bins_out,
            }
    except Exception as e:
        logger.warning("Could not list Homebox bins via API: %s", e)
        return {
            "homebox_base_url": target_base,
            "homebox_locations_url": target_base,
            "authenticated": False,
            "next_bin_id": "BIN-001",
            "total_bins": 0,
            "bins": [],
            "error": str(e),
        }
