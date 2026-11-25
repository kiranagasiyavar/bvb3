"""Configuration constants, vocabulary, and patterns for Anticipatory Commerce Agent.
"""
import os
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
CATALOGUE_PATH = BASE_DIR / "catalogue.csv"
DEV_DATA_PATH = BASE_DIR / "dev.jsonl"

# Categories without size in catalogue (backpacks, caps, headphones, wallets, watches)
UNSIZED_CATEGORIES = {"backpacks", "caps", "headphones", "wallets", "watches"}

# Sized categories
FOOTWEAR_CATEGORIES = {"running shoes", "sneakers", "sandals"}
JEANS_CATEGORIES = {"jeans"}
APPAREL_CATEGORIES = {"t-shirts", "shirts", "kurtas", "dresses", "hoodies", "jackets", "track pants"}

# Catalogue Brands
BRANDS = [
    "Audora", "Carrafel", "Horavo", "Kesar Loom", "Kudova", "Ledgerly",
    "Loomsy", "Mehrin", "Northweft", "Pacevo", "Packwise", "Sonquil",
    "Strydo", "Tanaro", "Tikkra", "Urbanyx", "Wavlo", "Zentrail"
]

# Category regex patterns with alias & synonym expansion
CATEGORY_PATTERNS = [
    ("running shoes", [
        r"\brunning\s+shoes?\b", r"\brunning\s+sneakers?\b", r"\brunning\s+kicks\b",
        r"\bjogging\s+shoes?\b", r"\brunning\b", r"\brunners?\b", r"\btempo\s+shoes?\b",
        r"\btrainers?\b"
    ]),
    ("track pants", [
        r"\btrack\s+pants?\b", r"\btrackpants?\b", r"\bjoggers?\b", r"\bsweatpants?\b",
        r"\btrack\s+trousers?\b"
    ]),
    ("t-shirts", [
        r"\bt[\s\-_]+shirts?\b", r"\btshirt\b", r"\btees?\b", r"\bcrewneck\s+tee\b"
    ]),
    ("sandals", [
        r"\bsandals?\b", r"\bslides?\b", r"\bfloaters?\b", r"\bchappals?\b",
        r"\bslippers?\b", r"\bflip\s+flops?\b"
    ]),
    ("hoodies", [
        r"\bhooded\s+sweatshirts?\b", r"\bhooded\s+pullovers?\b", r"\bhoodies?\b",
        r"\bsweatshirts?\b", r"\bpullovers?\b"
    ]),
    ("sneakers", [
        r"\bcasual\s+sneakers?\b", r"\bcasual\s+shoes?\b", r"\bcanvas\s+shoes?\b",
        r"\bsneakers?\b", r"\bkicks\b"
    ]),
    ("shirts", [
        r"\bcasual\s+shirts?\b", r"\bformal\s+shirts?\b", r"\bbutton\s+downs?\b",
        r"\bshirts?\b"
    ]),
    ("jeans", [
        r"\bjeans?\b", r"\bdenims?\b"
    ]),
    ("kurtas", [
        r"\bkurtas?\b", r"\bkurtis?\b"
    ]),
    ("dresses", [
        r"\bdress(?:es)?\b", r"\bfrocks?\b", r"\bgowns?\b"
    ]),
    ("jackets", [
        r"\bjackets?\b", r"\bcoats?\b", r"\bblazers?\b", r"\bbombers?\b"
    ]),
    ("backpacks", [
        r"\bbackpacks?\b", r"\bbag\s*packs?\b", r"\brucksacks?\b", r"\bbags?\b"
    ]),
    ("caps", [
        r"\bcaps?\b", r"\bhats?\b"
    ]),
    ("headphones", [
        r"\bheadphones?\b", r"\bearphones?\b", r"\bearbuds?\b", r"\bheadsets?\b"
    ]),
    ("wallets", [
        r"\bwallets?\b", r"\bpurses?\b"
    ]),
    ("watches", [
        r"\bwrist\s*watch(?:es)?\b", r"\bwatch(?:es)?\b", r"\btimepieces?\b", r"\bwristwatch(?:es)?\b"
    ])
]

# Colour regex patterns with Hindi-English code-mixed support
COLOUR_PATTERNS = [
    ("navy", [r"\bnavy\s+blue\b", r"\bnavy\b"]),
    ("olive", [r"\bolive\s+green\b", r"\bolive\b"]),
    ("black", [r"\bblack\b", r"\bkaala\b", r"\bkala\b", r"\bkaali\b", r"\bkale\b"]),
    ("blue", [r"\bblue\b", r"\bneela\b", r"\bnila\b", r"\bneeli\b", r"\bneele\b"]),
    ("brown", [r"\bbrown\b", r"\bbhoora\b", r"\bbhura\b"]),
    ("gold", [r"\bgolden?\b"]),
    ("green", [r"\bgreen\b", r"\bhara\b", r"\bhari\b", r"\bhare\b"]),
    ("grey", [r"\bgrey\b", r"\bgray\b"]),
    ("maroon", [r"\bmaroon\b"]),
    ("pink", [r"\bpink\b", r"\bgulaabi\b", r"\bgulabi\b"]),
    ("red", [r"\bred\b", r"\blaal\b", r"\blal\b"]),
    ("silver", [r"\bsilver\b"]),
    ("tan", [r"\btan\b"]),
    ("white", [r"\bwhite\b", r"\bsafed\b"]),
    ("yellow", [r"\byellow\b", r"\bpeela\b", r"\bpila\b", r"\bpeeli\b", r"\bpeele\b"]),
    ("beige", [r"\bbeige\b"])
]

# Number mappings
NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000
}

HINDI_SIZE_NUMBERS = {
    "che": "6", "chhe": "6", "saat": "7", "aath": "8", "nau": "9", "das": "10", "gyaarah": "11"
}

# Natural language correction phrases
CORRECTION_PATTERN = re.compile(
    r"\b(?:oops|sorry|no\s+wait|scratch\s+that|wait[,\s]+i\s+meant?|i\s+meant?|or\s+rather|rather|actually|make\s+that|make\s+it|change\s+that\s+to|no\s+no|nahi|matlab)\b",
    re.IGNORECASE
)

# Closing triggers that indicate the shopper has finished specifying constraints
CLOSING_TRIGGER = re.compile(
    r"\b(?:for\s+(?:a|the|my|office)|as\s+a|nothing\s+too\s+flashy|nothing|if\s+you\s+have\s+it|if\s+you|need\s+it\s+this\s+week|need\s+it|please|thanks?|thank\s+you|milega|chahiye|dikhao\s+na|dikhao|hai\s+kya)\b",
    re.IGNORECASE
)

# Filler words and conjunctions that indicate incomplete intent or pending constraints
PENDING_WORDS = {"and", "oh", "also", "um", "uh", "one", "more", "thing", "with", "like", "in"}

# Rezolve Labs API Config
REZOLVE_API_BASE = os.environ.get("REZOLVE_API_BASE", "https://api.rezolvelabs.com/api/v1")
REZOLVE_API_KEY = os.environ.get("REZOLVE_API_KEY", "")
REZOLVE_KB_ID = os.environ.get("REZOLVE_KB_ID", "")
