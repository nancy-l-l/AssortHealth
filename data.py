from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    specialty: str

@dataclass(frozen=True)
class Slots:
    id: str
    provider_id: str
    start_iso: str

PROVIDERS: List[Provider] = [
    Provider(id="p1", name="Dr. Smith", specialty="Cardiology"),
    Provider(id="p2", name="Dr. Johnson", specialty="Dermatology"),
    Provider(id="p3", name="Dr. Williams", specialty="Orthopedics"),
]
    
SLOTS: List[Slots] = [
    Slots(id="s1", provider_id="p1", start_iso="2024-07-01T09:00:00Z"),
    Slots(id="s2", provider_id="p1", start_iso="2024-07-01T10:00:00Z"),
    Slots(id="s3", provider_id="p2", start_iso="2024-07-01T11:00:00Z"),
    Slots(id="s4", provider_id="p3", start_iso="2024-07-01T12:00:00Z"),
]

    
    