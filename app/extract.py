"""Parser child: bounded resources; UTF-8 disk output; ASCII-safe legacy stdout."""
import json
import os
import sys
from pathlib import Path

def main():
    from . import limits
    cfg = json.loads(os.environ["WORKROOM_PARSER_LIMITS"]) if os.environ.get("WORKROOM_PARSER_LIMITS") else {k:s[0] for k,s in limits.FIELDS.items()}
    try:
        try:
            import resource
            memory = cfg["parser_memory_mb"] * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
            resource.setrlimit(resource.RLIMIT_CPU, (cfg["parser_seconds"], cfg["parser_seconds"]+1))
        except ImportError:
            pass
        from .documents import _extract
        parts, note = _extract(Path(sys.argv[1]), sys.argv[2], cfg)
        data = {"parts": parts, "note": note}
    except limits.DocumentLimit as e:
        data = {"error": str(e), "limited": True}
    except MemoryError:
        data = {"error": "Parser-RAM-Grenze erreicht.", "limited": True}
    except ValueError as e:
        data = {"error": str(e)}
    except Exception:
        data = {"error": "Dateiformat beschädigt oder nicht unterstützt. Original bei Bedarf ohne Textindex ablegen."}
    if len(sys.argv) > 3:
        with Path(sys.argv[3]).open("w", encoding="utf-8") as output:
            json.dump(data, output, ensure_ascii=False)
    else:
        print(json.dumps(data, ensure_ascii=True))

if __name__ == "__main__":
    main()
