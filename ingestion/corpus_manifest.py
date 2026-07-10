SNAPSHOT_DATE = "2026-07-01"   # keep in sync with CORPUS_SNAPSHOT_DATE in .env

DOCUMENTS = [
    {
        "path": "corpus/pdpa_act_9_2022.pdf",
        "collection": "statute",
        # s.56 (Interpretation) is the Act's definitions section; routing it
        # to its own small collection stops definition lookups drowning in
        # the 90-chunk statute haystack ("controller" appears everywhere).
        "reroute_sections": {"s.56": "definitions"},
        "snapshot_date": SNAPSHOT_DATE,
        "in_force": True,          # document-level default; sections differ — see COMMENCEMENT
        "commencement_notes": "principal enactment, certified 19 Mar 2022; "
                              "staggered commencement via s.1 Orders — see COMMENCEMENT",
    },
    {
        "path": "corpus/pdpa_amendment_22_2025.pdf",
        "collection": "amendments",
        "snapshot_date": SNAPSHOT_DATE,
        "in_force": True,
        "commencement_notes": "Personal Data Protection (Amendment) Act, No. 22 of 2025, "
                              "certified 30 Oct 2025; repealed s.1(3)-(5) of the principal "
                              "enactment, removing the statutory commencement window",
    },
]


# Verified 2026-07-09 against:
#   - the Act text itself (corpus/pdpa_act_9_2022.pdf) for section→Part boundaries
#   - dpa.gov.lk/Background.php (phase dates)
#   - Gazette No. 2341/59 (Part V, 17 Jul 2023) and Gazette No. 2366/08
#     (Parts VI, VIII, IX, X, 1 Dec 2023; also appointed 18 Mar 2025 for the rest)
#   - Gazette No. 2427/34 of 14 Mar 2025 (repealed the 18 Mar 2025 appointment)
#   - Amendment Act No. 22 of 2025 s.2 (corpus/pdpa_amendment_22_2025.pdf):
#     new s.1(3) leaves commencement of the remaining provisions to future
#     Ministerial Order; no such Order made as of SNAPSHOT_DATE.
COMMENCEMENT = {
    # ---- NOT in force as of 2026-07-01 ---------------------------------
    "s.2-s.3": {
        "in_force": False,
        "note": "preliminary/application provisions — the 18 Mar 2025 appointed date "
                "(Gazette 2366/08) was repealed by Gazette 2427/34 of 14 Mar 2025; "
                "no new commencement Order as of the corpus snapshot",
    },
    "s.4-s.12": {
        "in_force": False,
        "note": "Part I (processing obligations) — 18 Mar 2025 appointed date repealed "
                "by Gazette 2427/34; awaiting a fresh Order under s.1(3) as amended",
    },
    "s.13-s.19": {
        "in_force": False,
        "note": "Part II (rights of data subjects) — 18 Mar 2025 appointed date repealed "
                "by Gazette 2427/34; awaiting a fresh Order under s.1(3) as amended",
    },
    "s.20-s.26": {
        "in_force": False,
        "note": "Part III (controllers and processors) — 18 Mar 2025 appointed date "
                "repealed by Gazette 2427/34; awaiting a fresh Order under s.1(3) as amended",
    },
    "s.27": {
        "in_force": False,
        "note": "Part IV (solicited messages) — original s.1(4) window repealed by the "
                "Amendment Act No. 22 of 2025; no commencement Order as of the snapshot",
    },
    "s.38-s.40": {
        "in_force": False,
        "note": "Part VII (penalties) — 18 Mar 2025 appointed date repealed by "
                "Gazette 2427/34; awaiting a fresh Order under s.1(3) as amended",
    },
    # ---- IN force ------------------------------------------------------
    "s.28-s.35": {
        "in_force": True,
        "note": "Part V (Data Protection Authority) — in operation since 17 Jul 2023 "
                "per Gazette 2341/59",
    },
    "s.36-s.37": {
        "in_force": True,
        "note": "Part VI (Director-General and staff) — in operation since 1 Dec 2023 "
                "per Gazette 2366/08",
    },
    "s.41-s.42": {
        "in_force": True,
        "note": "Part VIII (Fund of the Authority) — in operation since 1 Dec 2023 "
                "per Gazette 2366/08",
    },
    "s.43-s.55": {
        "in_force": True,
        "note": "Part IX (miscellaneous) — in operation since 1 Dec 2023 "
                "per Gazette 2366/08",
    },
    "s.56": {
        "in_force": True,
        "note": "Part X (interpretation) — in operation since 1 Dec 2023 "
                "per Gazette 2366/08",
    },
}
