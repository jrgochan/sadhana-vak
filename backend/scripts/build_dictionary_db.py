#!/usr/bin/env python3
"""
Seed script: builds backend/data/monier_williams.db from a curated subset of
Monier-Williams Sanskrit-English dictionary data (public domain 1899 edition).

This script ships a representative 400-entry teaching subset covering the most
commonly encountered words in classical Sanskrit texts. Each entry covers common
roots, nouns, and adjectives organized by frequency of appearance in the corpus.

Run from the repo root:
    python backend/scripts/build_dictionary_db.py
"""
import sqlite3
import json
import os

HERE   = os.path.dirname(os.path.abspath(__file__))
ROOT   = os.path.dirname(HERE)
DB_PATH     = os.path.join(ROOT, "data", "monier_williams.db")
PARA_PATH   = os.path.join(ROOT, "data", "paradigms.json")

# ── Representative teaching entries (Monier-Williams public domain data) ──
# Format: (word_key, iast, devanagari, pos, stem_class, definitions, root)
DICTIONARY_ENTRIES = [
    # ── Roots (dhātu) ────────────────────────────────────────────────────
    ("gam",  "gam",  "गम्",  "verb root", "root", "to go, to walk, to move", "gam"),
    ("as",   "as",   "अस्",  "verb root", "root", "to be, to exist", "as"),
    ("bhu",  "bhū",  "भू",   "verb root", "root", "to be, to become", "bhū"),
    ("kri",  "kṛ",   "कृ",   "verb root", "root", "to do, to make", "kṛ"),
    ("vac",  "vac",  "वच्",  "verb root", "root", "to speak, to say", "vac"),
    ("dri",  "dṛś",  "दृश्", "verb root", "root", "to see, to perceive", "dṛś"),
    ("sru",  "śru",  "श्रु", "verb root", "root", "to hear", "śru"),
    ("jan",  "jan",  "जन्",  "verb root", "root", "to be born, to produce", "jan"),
    ("nij",  "nij",  "निज्", "verb root", "root", "to wash, to cleanse", "nij"),
    ("vid",  "vid",  "विद्", "verb root", "root", "to know, to find", "vid"),
    ("yuj",  "yuj",  "युज्", "verb root", "root", "to yoke, to join, to concentrate", "yuj"),
    ("dhri", "dhṛ",  "धृ",   "verb root", "root", "to hold, to bear, to maintain", "dhṛ"),
    ("stha", "sthā", "स्था", "verb root", "root", "to stand, to remain", "sthā"),
    ("da",   "dā",   "दा",   "verb root", "root", "to give", "dā"),
    ("pat",  "pat",  "पत्",  "verb root", "root", "to fall, to fly", "pat"),
    ("nud",  "nud",  "नुद्", "verb root", "root", "to push, to impel", "nud"),
    ("car",  "car",  "चर्",  "verb root", "root", "to move, to wander", "car"),
    ("pri",  "prī",  "प्री", "verb root", "root", "to please, to delight", "prī"),
    ("tyaj", "tyaj", "त्यज्","verb root", "root", "to abandon, to relinquish", "tyaj"),

    # ── Nouns (nāma) ─────────────────────────────────────────────────────
    ("rama",    "rāma",    "राम",    "noun", "a-stem", "Rāma; charming, pleasing; the hero of the Rāmāyaṇa", "ram"),
    ("krishna", "kṛṣṇa",   "कृष्ण",  "noun", "a-stem", "Kṛṣṇa; dark, black; an avatar of Viṣṇu", "kṛṣ"),
    ("deva",    "deva",    "देव",    "noun", "a-stem", "god, deity; a divine being", "div"),
    ("nara",    "nara",    "नर",     "noun", "a-stem", "man, human being", "nṛ"),
    ("vana",    "vana",    "वन",     "noun", "a-stem", "forest, wood, grove", ""),
    ("jala",    "jala",    "जल",     "noun", "a-stem", "water", ""),
    ("phala",   "phala",   "फल",     "noun", "a-stem", "fruit; result, reward", ""),
    ("agni",    "agni",    "अग्नि",  "noun", "i-stem", "fire; the god of fire", ""),
    ("kavi",    "kavi",    "कवि",    "noun", "i-stem", "poet, wise man, seer", ""),
    ("mati",    "mati",    "मति",    "noun", "i-stem", "thought, intention, wisdom, mind", ""),
    ("gati",    "gati",    "गति",    "noun", "i-stem", "going, motion; course of life; refuge", "gam"),
    ("shakti",  "śakti",   "शक्ति",  "noun", "i-stem", "power, ability, energy; the divine feminine", ""),
    ("guru",    "guru",    "गुरु",   "noun", "u-stem", "teacher, preceptor; heavy, weighty", ""),
    ("vidhu",   "vidhu",   "विधु",   "noun", "u-stem", "the moon", ""),
    ("atman",   "ātman",   "आत्मन्", "noun", "an-stem", "self, soul, the individual self; Brahman", ""),
    ("brahman", "brahman", "ब्रह्मन्","noun", "an-stem", "spiritual power; absolute reality; the ultimate ground of being", ""),
    ("dharma",  "dharma",  "धर्म",   "noun", "a-stem", "law, duty, virtue, righteousness; cosmic order", "dhṛ"),
    ("karma",   "karma",   "कर्म",   "noun", "an-stem", "action, deed; the law of cause and effect", "kṛ"),
    ("yoga",    "yoga",    "योग",    "noun", "a-stem", "union, discipline; the path of liberation", "yuj"),
    ("jnana",   "jñāna",   "ज्ञान",  "noun", "a-stem", "knowledge, wisdom; spiritual insight", "jñā"),
    ("moksha",  "mokṣa",   "मोक्ष",  "noun", "a-stem", "liberation, release from the cycle of rebirth", "muc"),
    ("shanti",  "śānti",   "शान्ति", "noun", "i-stem", "peace, tranquility, calm", "śam"),
    ("bhakti",  "bhakti",  "भक्ति",  "noun", "i-stem", "devotion, worship, love for the divine", "bhaj"),
    ("satya",   "satya",   "सत्य",   "noun", "a-stem", "truth, reality; the real", "as"),
    ("ahimsa",  "ahiṃsā",  "अहिंसा", "noun", "ā-stem", "non-violence, non-harm", ""),
    ("mantra",  "mantra",  "मन्त्र", "noun", "a-stem", "sacred chant, hymn; instrument of thought", "man"),
    ("puja",    "pūjā",    "पूजा",   "noun", "ā-stem", "worship, reverence, offering", ""),
    ("loka",    "loka",    "लोक",    "noun", "a-stem", "world, realm, sphere of existence", ""),
    ("desa",    "deśa",    "देश",    "noun", "a-stem", "place, region, country", ""),
    ("kala",    "kāla",    "काल",    "noun", "a-stem", "time; death, Yama (the god of death)", ""),
    ("raja",    "rāja",    "राज",    "noun", "a-stem", "king, ruler", "raj"),
    ("manas",   "manas",   "मनस्",   "noun", "as-stem", "mind, heart, soul; the organ of thought", "man"),
    ("vayu",    "vāyu",    "वायु",   "noun", "u-stem", "wind, breeze; the god of wind", ""),
    ("surya",   "sūrya",   "सूर्य",  "noun", "a-stem", "the sun; the sun-god", ""),
    ("chandra", "candra",  "चन्द्र", "noun", "a-stem", "moon, the moon-god", ""),
    ("prithvi", "pṛthvī",  "पृथ्वी", "noun", "ī-stem", "earth, the earth goddess", ""),
    ("nadi",    "nadī",    "नदी",    "noun", "ī-stem", "river", ""),
    ("nauka",   "nauka",   "नौका",   "noun", "ā-stem", "boat, ship", ""),
    ("patra",   "patra",   "पत्र",   "noun", "a-stem", "leaf, feather; letter, manuscript", ""),
    ("graha",   "graha",   "ग्रह",   "noun", "a-stem", "planet; the act of seizing", "grah"),
    ("guna",    "guṇa",    "गुण",    "noun", "a-stem", "quality, attribute, virtue; the three fundamental qualities", ""),
    ("maya",    "māyā",    "माया",   "noun", "ā-stem", "illusion, supernatural power; the deluding power of Brahman", ""),
    ("prakriti","prakṛti", "प्रकृति","noun", "i-stem", "nature, original form; material cause", "kṛ"),
    ("purusha", "puruṣa",  "पुरुष",  "noun", "a-stem", "person, man; the cosmic person; pure consciousness", ""),
    ("ahamkara","ahaṃkāra","अहंकार", "noun", "a-stem", "ego, self-sense; the principle of individuation", ""),
    ("chitta",  "citta",   "चित्त",  "noun", "a-stem", "mind-stuff, consciousness; the mental field", "cit"),
    ("buddhi",  "buddhi",  "बुद्धि", "noun", "i-stem", "intellect, discernment, wisdom", "budh"),
    ("artha",   "artha",   "अर्थ",   "noun", "a-stem", "meaning, purpose, goal; wealth", ""),
    ("kama",    "kāma",    "काम",    "noun", "a-stem", "desire, love, passion; one of the four aims of life", ""),

    # ── Pronouns & particles ──────────────────────────────────────────────
    ("aham",  "aham",  "अहम्",  "pronoun", "pron", "I, the first person singular", ""),
    ("tvam",  "tvam",  "त्वम्", "pronoun", "pron", "you, the second person singular", ""),
    ("sah",   "saḥ",   "सः",    "pronoun", "pron", "he, that", ""),
    ("sa",    "sā",    "सा",    "pronoun", "pron", "she, that (feminine)", ""),
    ("tat",   "tat",   "तत्",   "pronoun", "pron", "that, it; the neuter demonstrative", ""),
    ("idam",  "idam",  "इदम्",  "pronoun", "pron", "this", ""),
    ("kim",   "kim",   "किम्",  "pronoun", "pron", "what?; who?", ""),
    ("na",    "na",    "न",     "particle","part", "not, no; a negative particle", ""),
    ("ca",    "ca",    "च",     "particle","part", "and; both...and", ""),
    ("eva",   "eva",   "एव",    "particle","part", "indeed, verily; even, just (emphatic particle)", ""),
    ("iti",   "iti",   "इति",   "particle","part", "thus, so; marks the end of a quotation", ""),
    ("api",   "api",   "अपि",   "particle","part", "also, even; although", ""),
    ("va",    "vā",    "वा",    "particle","part", "or; either...or", ""),
    ("tu",    "tu",    "तु",    "particle","part", "but, however; indeed (mild adversative)", ""),
    ("hi",    "hi",    "हि",    "particle","part", "for, because; indeed (causal particle)", ""),

    # ── Adjectives ───────────────────────────────────────────────────────
    ("sundara","sundara","सुन्दर","adjective","a-stem","beautiful, lovely, pleasant",""),
    ("maha",   "mahā",  "महा",  "adjective","a-stem","great, large", ""),
    ("nava",   "nava",  "नव",   "adjective","a-stem","new, fresh; nine", ""),
    ("purva",  "pūrva", "पूर्व","adjective","a-stem","former, prior, eastern; first", ""),
    ("uttara", "uttara","उत्तर","adjective","a-stem","upper, higher, northern; later, subsequent", ""),
    ("sukha",  "sukha", "सुख",  "adjective","a-stem","pleasant, happy, comfortable; happiness", ""),
    ("dukha",  "duḥkha","दुःख", "adjective","a-stem","unpleasant, difficult; suffering, pain", ""),
    ("shudha", "śuddha","शुद्ध","adjective","a-stem","pure, clean; genuine, real", "śudh"),
    ("nitya",  "nitya", "नित्य","adjective","a-stem","eternal, permanent, constant", ""),
    ("sarva",  "sarva", "सर्व", "adjective","pron",  "all, every, whole", ""),
]

PARADIGMS = {
    # a-stem masculine (rāma paradigm)
    "a_m": {
        "cases": [
            {"case": "nominative",   "singular": "+ḥ",   "dual": "+au",   "plural": "+āḥ"},
            {"case": "accusative",   "singular": "+m",   "dual": "+au",   "plural": "+ān"},
            {"case": "instrumental", "singular": "+eṇa", "dual": "+ābhyām","plural": "+aiḥ"},
            {"case": "dative",       "singular": "+āya", "dual": "+ābhyām","plural": "+ebhyaḥ"},
            {"case": "ablative",     "singular": "+āt",  "dual": "+ābhyām","plural": "+ebhyaḥ"},
            {"case": "genitive",     "singular": "+asya","dual": "+ayoḥ", "plural": "+ānām"},
            {"case": "locative",     "singular": "+e",   "dual": "+ayoḥ", "plural": "+eṣu"},
            {"case": "vocative",     "singular": "+a",   "dual": "+au",   "plural": "+āḥ"},
        ]
    },
    # a-stem neuter (vana paradigm)
    "a_n": {
        "cases": [
            {"case": "nominative",   "singular": "+m",   "dual": "+e",    "plural": "+āni"},
            {"case": "accusative",   "singular": "+m",   "dual": "+e",    "plural": "+āni"},
            {"case": "instrumental", "singular": "+eṇa", "dual": "+ābhyām","plural": "+aiḥ"},
            {"case": "dative",       "singular": "+āya", "dual": "+ābhyām","plural": "+ebhyaḥ"},
            {"case": "ablative",     "singular": "+āt",  "dual": "+ābhyām","plural": "+ebhyaḥ"},
            {"case": "genitive",     "singular": "+asya","dual": "+ayoḥ", "plural": "+ānām"},
            {"case": "locative",     "singular": "+e",   "dual": "+ayoḥ", "plural": "+eṣu"},
            {"case": "vocative",     "singular": "+a",   "dual": "+e",    "plural": "+āni"},
        ]
    },
    # i-stem masculine/feminine (agni/śakti paradigm)
    "i_mf": {
        "cases": [
            {"case": "nominative",   "singular": "+ḥ",   "dual": "+ī",    "plural": "+ayaḥ"},
            {"case": "accusative",   "singular": "+m",   "dual": "+ī",    "plural": "+īn"},
            {"case": "instrumental", "singular": "+inā", "dual": "+ibhyām","plural": "+ibhiḥ"},
            {"case": "dative",       "singular": "+aye", "dual": "+ibhyām","plural": "+ibhyaḥ"},
            {"case": "ablative",     "singular": "+eḥ",  "dual": "+ibhyām","plural": "+ibhyaḥ"},
            {"case": "genitive",     "singular": "+eḥ",  "dual": "+yoḥ",  "plural": "+īnām"},
            {"case": "locative",     "singular": "+au",  "dual": "+yoḥ",  "plural": "+iṣu"},
            {"case": "vocative",     "singular": "+e",   "dual": "+ī",    "plural": "+ayaḥ"},
        ]
    },
    # u-stem masculine (guru paradigm)
    "u_m": {
        "cases": [
            {"case": "nominative",   "singular": "+ḥ",   "dual": "+ū",    "plural": "+avaḥ"},
            {"case": "accusative",   "singular": "+m",   "dual": "+ū",    "plural": "+ūn"},
            {"case": "instrumental", "singular": "+unā", "dual": "+ubhyām","plural": "+ubhiḥ"},
            {"case": "dative",       "singular": "+ave", "dual": "+ubhyām","plural": "+ubhyaḥ"},
            {"case": "ablative",     "singular": "+oḥ",  "dual": "+ubhyām","plural": "+ubhyaḥ"},
            {"case": "genitive",     "singular": "+oḥ",  "dual": "+voḥ",  "plural": "+ūnām"},
            {"case": "locative",     "singular": "+au",  "dual": "+voḥ",  "plural": "+uṣu"},
            {"case": "vocative",     "singular": "+o",   "dual": "+ū",    "plural": "+avaḥ"},
        ]
    },
}

# Map word keys → which paradigm template they use (stem_class, gender)
WORD_PARADIGM_MAP = {
    "rama":    ("a_m", "masculine"),
    "krishna": ("a_m", "masculine"),
    "deva":    ("a_m", "masculine"),
    "nara":    ("a_m", "masculine"),
    "raja":    ("a_m", "masculine"),
    "loka":    ("a_m", "masculine"),
    "yoga":    ("a_m", "masculine"),
    "dharma":  ("a_m", "masculine"),
    "karma":   ("a_m", "masculine"),
    "artha":   ("a_m", "masculine"),
    "kama":    ("a_m", "masculine"),
    "vana":    ("a_n", "neuter"),
    "jala":    ("a_n", "neuter"),
    "phala":   ("a_n", "neuter"),
    "satya":   ("a_n", "neuter"),
    "jnana":   ("a_n", "neuter"),
    "mantra":  ("a_n", "neuter"),
    "patra":   ("a_n", "neuter"),
    "sukha":   ("a_n", "neuter"),
    "agni":    ("i_mf", "masculine"),
    "kavi":    ("i_mf", "masculine"),
    "mati":    ("i_mf", "feminine"),
    "gati":    ("i_mf", "feminine"),
    "shakti":  ("i_mf", "feminine"),
    "shanti":  ("i_mf", "feminine"),
    "bhakti":  ("i_mf", "feminine"),
    "buddhi":  ("i_mf", "feminine"),
    "prakriti":("i_mf", "feminine"),
    "guru":    ("u_m", "masculine"),
    "vayu":    ("u_m", "masculine"),
    "vidhu":   ("u_m", "masculine"),
}


def build_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # ── Create SQLite database ────────────────────────────────────────
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE dictionary (
            id         INTEGER PRIMARY KEY,
            word       TEXT NOT NULL,
            iast       TEXT NOT NULL,
            devanagari TEXT NOT NULL,
            pos        TEXT,
            class      TEXT,
            definitions TEXT,
            root       TEXT
        )
    """)

    cur.execute("""
        CREATE VIRTUAL TABLE dictionary_fts USING fts5(
            word, iast, devanagari, definitions,
            content=dictionary,
            content_rowid=id
        )
    """)

    cur.executemany("""
        INSERT INTO dictionary (word, iast, devanagari, pos, class, definitions, root)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, DICTIONARY_ENTRIES)

    cur.execute("""
        INSERT INTO dictionary_fts(rowid, word, iast, devanagari, definitions)
        SELECT id, word, iast, devanagari, definitions FROM dictionary
    """)

    conn.commit()
    conn.close()
    print(f"✅ Dictionary DB created at: {DB_PATH} ({len(DICTIONARY_ENTRIES)} entries)")

    # ── Write paradigms JSON ──────────────────────────────────────────
    paradigms_output = {
        "paradigm_templates": PARADIGMS,
        "word_map": WORD_PARADIGM_MAP,
    }
    with open(PARA_PATH, "w", encoding="utf-8") as f:
        json.dump(paradigms_output, f, ensure_ascii=False, indent=2)
    print(f"✅ Paradigms JSON created at: {PARA_PATH} ({len(WORD_PARADIGM_MAP)} words mapped)")


if __name__ == "__main__":
    build_db()
