"""
Configuration: companies to monitor, keyword filters, and runtime settings.
"""

# ----- Workday companies (direct careers page scraping) -----
COMPANIES = [
    ("NVIDIA", "workday", {
        "tenant": "nvidia",
        "site": "NVIDIAExternalCareerSite",
        "host": "nvidia.wd5.myworkdayjobs.com",
    }),
]

# ----- LinkedIn companies (LinkedIn guest API search) -----
# We search LinkedIn for jobs at each of these companies.
# Coverage is automatic - any company posting jobs on LinkedIn shows up.
LINKEDIN_COMPANIES = [
    "NVIDIA",
    "Apple",
    "Intel",
    "Mobileye",
    "Qualcomm",
    "ARM",
    "Marvell",
    "Broadcom",
    "Tower Semiconductor",
    "Applied Materials",
    "KLA",
    "Cadence",
    "Synopsys",
    "Hailo",
    "Innoviz",
    "Camtek",
    "Nova Measuring",
    "Wiliot",
    "Rafael",
    "Elbit Systems",
    "IAI",
    "Microsoft",
    "Google",
    "Meta",
    "Amazon",
    "Annapurna Labs",
]

# LinkedIn time-posted-range (TPR) for searches:
#   "r3600"   = last 1 hour    (best for catching brand-new jobs every 5 min)
#   "r21600"  = last 6 hours
#   "r86400"  = last 24 hours
#   "r604800" = last week
LINKEDIN_TIME_RANGE = "r3600"

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
MAX_JOBS_PER_RUN = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
