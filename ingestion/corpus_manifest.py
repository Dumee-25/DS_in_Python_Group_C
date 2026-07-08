SNAPSHOT_DATE = "2026-07-01"   # keep in sync with CORPUS_SNAPSHOT_DATE in .env

DOCUMENTS = [
    {
        "path": "corpus/pdpa_act_9_2022.pdf",
        "collection": "statute",
        "snapshot_date": SNAPSHOT_DATE,
        "in_force": True,          # document-level default; sections may differ
        "commencement_notes": "principal enactment; staggered commencement via s.1(2) Orders",
    },
    {
        "path": "corpus/pdpa_amendment_22_2025.pdf",
        "collection": "amendments",
        "snapshot_date": SNAPSHOT_DATE,
        "in_force": True,
        "commencement_notes": "amends the principal Act; check its own commencement clause",
    },
    
]


COMMENCEMENT = {
    "s.20-s.27": {
        "in_force": False,
        "note": "PLACEHOLDER — verify which Part these sections belong to and "
                "whether a s.1(2) Order has appointed their commencement date",
    },
    "s.35": {
        "in_force": True,
        "note": "PLACEHOLDER — verify the actual Order number and date",
    },
}
