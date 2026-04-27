"""
Configuration: companies to monitor, keyword filters, and runtime settings.

Edit this file to add/remove companies or tune which jobs you want to be notified about.
"""

# ----- Companies to monitor -----
# Each company is configured with the platform its careers page uses.
# Format: (company_name, platform, platform_specific_id)
#
# Platforms supported:
#   - "workday": NVIDIA, Apple, Qualcomm use Workday. ID is the careers site path.
#   - "greenhouse": Many startups use Greenhouse. ID is the company slug.
#   - "smartrecruiters": Some companies (Bosch, etc). ID is the company name.
#   - "intel_custom": Intel has a custom API
#   - "mobileye_custom": Mobileye uses a Comeet-based API

COMPANIES = [
    # name,      platform,           platform_id
    ("NVIDIA",   "workday",          {"tenant": "nvidia", "site": "NVIDIAExternalCareerSite", "host": "nvidia.wd5.myworkdayjobs.com"}),
    ("Apple",    "workday",          {"tenant": "apple",  "site": "AppleExternal",            "host": "jobs.apple.com"}),  # Apple uses a custom site, fallback handled
    ("Intel",    "intel_custom",     {}),
    ("Mobileye", "mobileye_custom",  {}),
    ("Qualcomm", "workday",          {"tenant": "qualcomm", "site": "External", "host": "qualcomm.wd5.myworkdayjobs.com"}),
    ("ARM",      "workday",          {"tenant": "arm",      "site": "External", "host": "arm.wd1.myworkdayjobs.com"}),
]

# ----- Location filters -----
# Only jobs in Israel are interesting. We match against the location text.
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
# A job must contain at least one of these in its title or description to pass.
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
    "silicon", "chip design", "soc", "cpu", "gpu",
    "electrical", "חשמל", "אלקטרוניקה",
    "signal", "אותות", "communication", "תקשורת",
    "low power", "power management",
]

# ----- Negative keywords -----
# A job is REJECTED if any of these appear in the title.
# (We check title only for negative keywords to avoid rejecting good jobs that mention "senior team" etc in the description.)
NEGATIVE_TITLE_KEYWORDS = [
    "senior", "principal", "staff", "lead", "manager", "director",
    "vp ", "vice president", "head of", "chief",
    "expert", "מומחה",
    "5+ years", "7+ years", "10+ years",
]

# ----- Description-based negative phrases -----
# Strong rejection signals in the description text
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
REQUEST_TIMEOUT = 20  # seconds
MAX_JOBS_PER_RUN = 20  # safety: don't spam telegram on first run
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
