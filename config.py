"""
Configuration: companies to monitor, keyword filters, and runtime settings.

Edit this file to add/remove companies or tune which jobs you want to be notified about.
"""

# ----- Companies to monitor -----
# Format: (company_name, platform, platform_specific_id)
#
# Platforms supported:
#   - "workday": NVIDIA, Qualcomm, ARM use Workday
#   - "intel_custom": Intel uses Phenom (currently disabled)
#   - "mobileye_custom": Mobileye Comeet (currently disabled)
#
# DISABLED for now (need API discovery):
#   - Apple: uses custom careers system, not Workday
#   - Intel: Phenom platform with strict anti-bot, needs HTML scraping
#   - Mobileye: Comeet API ID needs to be found

COMPANIES = [
    # name,      platform,   platform_id
    ("NVIDIA",   "workday",  {"tenant": "nvidia",   "site": "NVIDIAExternalCareerSite", "host": "nvidia.wd5.myworkdayjobs.com"}),
    ("Qualcomm", "workday",  {"tenant": "qualcomm", "site": "External",                 "host": "qualcomm.wd5.myworkdayjobs.com"}),
    ("ARM",      "workday",  {"tenant": "arm",      "site": "External",                 "host": "arm.wd1.myworkdayjobs.com"}),

    # Disabled until we find correct endpoints:
    # ("Apple",    "apple_custom",    {}),
    # ("Intel",    "intel_custom",    {}),
    # ("Mobileye", "mobileye_custom", {}),
]

# ----- Location filters -----
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
    "matam", "מת\"ם",
]

# ----- Positive keywords -----
POSITIVE_KEYWORDS = [
    # Student / early career
    "student", "intern", "internship", "סטודנט", "סטודנטית", "מתמחה",
    "junior", "ג'וניור", "graduate", "entry level", "entry-level",
    "new grad", "early career", "early-career",

    # Electrical engineering relevant
    "hardware", "חומרה",
    "fpga", "vlsi", "asic", "rtl", "verilog", "systemverilog",
    "firmware", "embedded", "מוטמע",
    "dsp", "rf", "analog", "אנלוגי", "digital design",
    "verification", "וריפיקציה", "physical design",
    "silicon", "chip design", "soc",
    "electrical", "חשמל", "אלקטרוניקה",
    "signal", "אותות", "communication", "תקשורת",
    "low power", "power management",
]

# ----- Negative title keywords -----
NEGATIVE_TITLE_KEYWORDS = [
    "senior", "principal", "staff", "lead", "manager", "director",
    "vp ", "vice president", "head of", "chief",
    "expert", "מומחה",
    "5+ years", "7+ years", "10+ years",
]

NEGATIVE_DESCRIPTION_PHRASES = [
    "5+ years of experience",
    "7+ years of experience",
    "10+ years of experience",
    "minimum of 5 years",
    "minimum of 7 years",
    "minimum of 10 years",
]

# ----- Runtime settings -----
DB_PATH = "seen_jobs.db"
REQUEST_TIMEOUT = 20
MAX_JOBS_PER_RUN = 20
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
