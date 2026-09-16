"""Small, Qt-independent pieces of the desktop pet."""
from __future__ import annotations

import json
from pathlib import Path

DEFAULTS = {"scale": 1.0, "wander": True, "topmost": True, "quiet": False}


def clamp_position(x, y, width, height, area):
    left, top, right, bottom = area
    return (round(max(left, min(x, max(left, right - width)))),
            round(max(top, min(y, max(top, bottom - height)))))


def read_settings(path: Path):
    result = DEFAULTS.copy()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return result
        scale = data.get("scale")
        if isinstance(scale, (int, float)) and not isinstance(scale, bool):
            result["scale"] = max(0.65, min(1.6, scale))
        for key in ("wander", "topmost", "quiet"):
            if isinstance(data.get(key), bool):
                result[key] = data[key]
        position = data.get("position")
        if (isinstance(position, list) and len(position) == 2
                and all(isinstance(n, int) and not isinstance(n, bool) for n in position)):
            result["position"] = position
    except (OSError, ValueError, TypeError):
        pass
    return result


def write_settings(path: Path, settings):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
