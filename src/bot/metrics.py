import json
import sys
import time

_NAMESPACE = "ScryfallBot"


def record_metric(name: str, dimensions: dict[str, str] | None = None) -> None:
    try:
        dimension_keys = list(dimensions.keys()) if dimensions else []
        entry: dict = {
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": _NAMESPACE,
                        "Dimensions": [dimension_keys],
                        "Metrics": [{"Name": name, "Unit": "Count"}],
                    }
                ],
            },
            name: 1,
            **(dimensions or {}),
        }
        print(json.dumps(entry))
    except Exception as err:
        print(f"Failed to record metric: {name}", err, file=sys.stderr)
