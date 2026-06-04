import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
source_path = ROOT / "data" / "raw" / "events" / "github_events.jsonl"
target_path = ROOT / "data" / "processed" / "push_events.json"
environment = os.getenv("APP_ENV", "local")

events = []

with source_path.open() as source:
    for line in source:
        events.append(json.loads(line))

push_events = [event for event in events if event["type"] == "PushEvent"]

target_path.parent.mkdir(parents=True, exist_ok=True)

with target_path.open("w") as target:
    json.dump(push_events, target, indent=2)

print(f"Environment: {environment}")
print(f"Eventos leidos:          {len(events)}")
print(f"PushEvents encontrados:  {len(push_events)}")
print(f"Salida: {target_path}")
