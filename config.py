"""
Configuration: companies to monitor, keyword filters, and runtime settings.
"""

# ----- Direct-scrape companies -----
# Each entry: (display_name, platform, platform_id_dict)
# Companies can also appear in LINKEDIN_COMPANIES below — coverage between
# the two sources is imperfect, and main.py's dedup uses (company, url, title)
# so a job that appears on both sources is intentionally surfaced from each
# (different URLs -> different hashes).
#
# Notes:
# - Mobileye sits behind CloudFront bot detection that we can't bypass
#   without a headless browser. Direct scraper currently 403s. Kept in
#   case detection relaxes; LinkedIn covers Mobileye in the meantime.
# - Qualcomm's Eightfold endpoint also returns 403 ("Not authorized for
#   PCSX"). Kept for the same reason.
COMPANIES = [
    # Workday-based careers pages
    ("NVIDIA",            "workday",       {"tenant": "nvidia",            "site": "NVIDIAExternalCareerSite", "host": "nvidia.wd5.myworkdayjobs.com"}),
    ("Intel",             "workday",       {"tenant": "intel",             "site": "External",                 "host": "intel.wd1.myworkdayjobs.com"}),
    ("Marvell",           "workday",       {"tenant": "marvell",           "site": "MarvellCareers",           "host": "marvell.wd1.myworkdayjobs.com"}),
    ("Broadcom",          "workday",       {"tenant": "broadcom",          "site": "External_Career",          "host": "broadcom.wd1.myworkdayjobs.com"}),
    ("Samsung",           "workday",       {"tenant": "sec",               "site": "Samsung_Careers",          "host": "sec.wd3.myworkdayjobs.com"}),
    ("Motorola",          "workday",       {"tenant": "motorolasolutions", "site": "Careers",                  "host": "motorolasolutions.wd5.myworkdayjobs.com"}),

    # Oracle Recruiting Cloud HCM-based careers pages
    ("Texas Instruments", "oracle_hcm",    {"host": "edbz.fa.us2.oraclecloud.com",                              "site": "CX"}),

    # Apple's own careers site (server-side rendered HTML)
    ("Apple",             "apple_direct",  {}),

    # Google's own careers site (server-side rendered HTML)
    ("Google",            "google_direct", {}),

    # Phenom-hosted careers pages (Mobileye currently 403s)
    ("Mobileye",          "phenom",        {"host": "careers.mobileye.com",                                    "country": "Israel"}),

    # Eightfold AI-hosted careers pages (Qualcomm currently 403s)
    ("Qualcomm",          "eightfold",     {"tenant": "qualcomm",          "domain": "qualcomm.com",           "location": "Israel"}),
]

# ----- LinkedIn companies (LinkedIn guest API) -----
# Includes companies also scraped directly above — coverage between the two
# sources isn't identical, so we keep both for breadth.
LINKEDIN_COMPANIES = [
    "Google",
    "Amazon",
    "Apple",
    "Qualcomm",
    "Mobileye",
    "Microsoft",
    "Meta",
    "ARM",
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
    "Texas Instruments",
    "Valens",
    "Altair Semiconductor",
    "Nuvoton",
    "Renesas",
    "Winbond",
    "Cisco",
    "MaxLinear",
    "Infinidat",
    "Annapurna Labs",
]

# 24-hour window: catches all jobs posted today, dedup ensures no duplicates
LINKEDIN_TIME_RANGE = "r86400"

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
    "hod hasharon", "הוד השרון",
    "caesarea", "קיסריה",
    "gedera", "גדרה",
]

# ----- TIER 1: Student-level indicators (must be in title) -----
STUDENT_LEVEL_TITLE_KEYWORDS = [
    "student", "intern", "internship",
    "סטודנט", "סטודנטית", "מתמחה",
    "working student", "part time", "part-time",
]

# ----- TIER 2: SIL's specific fields (chip design / verification / analog / board) -----
# Tighter than before - based on what your SIL told us he's looking for
FIELD_RELEVANCE_KEYWORDS = [
    # Chip design
    "chip design", "asic", "vlsi", "rtl", "verilog", "systemverilog",
    "soc", "silicon", "physical design", "digital design", "logic design",
    "place and route", "synthesis", "timing", "floorplan",
    "תכנון שבבים", "vlsi", "אסיק",

    # Verification
    "verification", "וריפיקציה", "ולידציה",
    "validation", "uvm", "test bench", "testbench", "formal",

    # Analog
    "analog", "אנלוגי", "mixed signal", "mixed-signal",
    "rf ", " rf", "rfic",

    # Board design / hardware
    "board design", "pcb", "layout",
    "hardware", "חומרה",
    "fpga",
    "embedded", "מוטמע",
    "firmware",
    "circuit", "מעגל",
    "post silicon", "post-silicon",
    "low power",
    "power management",
    "dsp",
    "electrical engineer", "חשמל", "אלקטרוניקה",
]

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

NEGATIVE_DESCRIPTION_PHRASES = [
    "5+ years of experience", "7+ years of experience", "10+ years of experience",
    "minimum of 5 years", "minimum of 7 years", "minimum of 10 years",
    "at least 5 years", "at least 7 years", "at least 10 years",
    "phd required", "ph.d. required", "doctorate required",
    "phd in ", "ph.d. in ",
]

DB_PATH = "seen_jobs.db"
REQUEST_TIMEOUT = 20
MAX_JOBS_PER_RUN = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
