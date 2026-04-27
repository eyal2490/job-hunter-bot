"""
Configuration: companies to monitor, keyword filters, and runtime settings.
"""

# ----- Companies to monitor -----
# Currently active:
#   - NVIDIA: works on Workday with Israel search filter
#
# Disabled (need different scraping approach):
#   - Qualcomm: their wd12 endpoint requires auth (returns total=0 for guests)
#   - ARM: uses Phenom (careers.arm.com), not Workday
#   - Apple: custom careers system, not Workday
#   - Intel: Phenom with strict anti-bot
#   - Mobileye: Comeet API ID needs to be found

COMPANIES = [
    ("NVIDIA", "workday", {
        "tenant": "nvidia",
        "site": "NVIDIAExternalCareerSite",
        "host": "nvidia.wd5.myworkdayjobs.com",
        "search_text": "Israel",
    }),
]

# ----- Location filters (final check on our side) -----
LOCATION_KEYWORDS = [
    "israel", "ישראל",
    "tel aviv", "תל אביב", "תל-אביב",
    "haifa", "חיפה",
    "jerusalem", "ירושלים",
    "yokneam", "יקנעם",
    "petah tikva", "petach tikva", "פתח תקווה",
    "herzliya", "הרצליה",
    "raanana", "ra'anana", "רעננה",
    "kfar saba", "כפר סבא",
    "ramat gan", "רמת גן",
    "beer sheva", "be'er sheva", "באר שבע",
    "netanya", "נתניה",
    "rehovot", "רחובות",
    "ness ziona", "נס ציונה",
    "rosh haayin", "ראש העין",
    "or yehuda", "אור יהודה",
    "matam", "מתם",
]

# ----- TIER 1: Student-level indicators (must appear in title) -----
STUDENT_LEVEL_TITLE_KEYWORDS = [
    "student", "intern", "internship",
    "סטודנט", "סטודנטית", "מתמחה",
    "working student", "part time", "part-time",
]

# ----- TIER 2: EE-relevant field indicators -----
FIELD_RELEVANCE_KEYWORDS = [
    "hardware", "חומרה",
    "fpga", "vlsi", "asic", "rtl", "verilog", "systemverilog",
    "firmware", "embedded", "מוטמע",
    "dsp", "rf", "analog", "אנלוגי",
    "digital design", "physical design",
    "verification", "וריפיקציה",
    "silicon", "chip design", "soc",
    "electrical", "חשמל", "אלקטרוניקה",
    "signal processing", "signal integrity",
    "communication", "תקשורת",
    "low power", "power management",
    "circuit", "מעגל",
    "pcb", "layout",
    "cpu", "gpu",
    "post silicon", "post-silicon",
    "validation", "ולידציה",
]

# ----- Negative title keywords -----
NEGATIVE_TITLE_KEYWORDS = [
    "senior", "principal", "staff", "lead ", " lead", "manager", "director",
    "vp ", "vice president", "head of", "chief",
    "expert", "מומחה",
    "phd", "ph.d", "ph d", "doctoral", "doctorate",
    "post doc", "postdoc", "post-doc",
    "5+ years", "7+ years", "10+ years",
    "marketing", "sales", "hr ", "human resources",
    "finance", "accounting", "legal",
    "recruiter", "recruiting",
]

# ----- Negative description phrases -----
NEGATIVE_DESCRIPTION_PHRASES = [
    "5+ years of experience", "7+ years of experience", "10+ years of experience",
    "minimum of 5 years", "minimum of 7 years", "minimum of 10 years",
    "at least 5 years", "at least 7 years", "at least 10 years",
    "phd required", "ph.d. required", "doctorate required",
    "phd in ", "ph.d. in ",
    "full-time position", "full time position",
    "this is a full-time", "this is a full time",
]

# ----- Runtime settings -----
DB_PATH = "seen_jobs.db"
REQUEST_TIMEOUT = 20
MAX_JOBS_PER_RUN = 20
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
