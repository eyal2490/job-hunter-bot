COMPANIES = [
    ("NVIDIA",            "workday",         {"tenant": "nvidia",            "site": "NVIDIAExternalCareerSite", "host": "nvidia.wd5.myworkdayjobs.com"}),
    ("Intel",             "workday",         {"tenant": "intel",             "site": "External",                 "host": "intel.wd1.myworkdayjobs.com"}),
    ("Marvell",           "workday",         {"tenant": "marvell",           "site": "MarvellCareers",           "host": "marvell.wd1.myworkdayjobs.com"}),
    ("Broadcom",          "workday",         {"tenant": "broadcom",          "site": "External_Career",          "host": "broadcom.wd1.myworkdayjobs.com"}),
    ("Samsung",           "workday",         {"tenant": "sec",               "site": "Samsung_Careers",          "host": "sec.wd3.myworkdayjobs.com"}),
    ("Motorola",          "workday",         {"tenant": "motorolasolutions", "site": "Careers",                  "host": "motorolasolutions.wd5.myworkdayjobs.com"}),
    ("Texas Instruments", "oracle_hcm",      {"host": "edbz.fa.us2.oraclecloud.com",                              "site": "CX"}),
    ("Apple",             "apple_direct",    {}),
    ("Amazon",            "amazon_direct",   {}),
    ("Innoviz",           "innoviz_direct",  {}),
    ("Valens",            "valens_direct",   {}),
    ("Altair Semiconductor", "altair_direct", {}),
    ("Mobileye",          "phenom",          {"host": "careers.mobileye.com",                                    "country": "Israel"}),
    ("Qualcomm",          "eightfold",       {"tenant": "qualcomm",          "domain": "qualcomm.com",           "location": "Israel"}),
]

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

LINKEDIN_TIME_RANGE = "r86400"

LOCATION_KEYWORDS = [
    "israel", "\u05d9\u05e9\u05e8\u05d0\u05dc",
    "tel aviv", "\u05ea\u05dc \u05d0\u05d1\u05d9\u05d1", "\u05ea\u05dc-\u05d0\u05d1\u05d9\u05d1",
    "haifa", "\u05d7\u05d9\u05e4\u05d4",
    "jerusalem", "\u05d9\u05e8\u05d5\u05e9\u05dc\u05d9\u05dd",
    "yokneam", "\u05d9\u05e7\u05e0\u05e2\u05dd",
    "petah tikva", "petach tikva", "\u05e4\u05ea\u05d7 \u05ea\u05e7\u05d5\u05d5\u05d4",
    "herzliya", "\u05d4\u05e8\u05e6\u05dc\u05d9\u05d4",
    "raanana", "ra'anana", "\u05e8\u05e2\u05e0\u05e0\u05d4",
    "kfar saba", "\u05db\u05e4\u05e8 \u05e1\u05d1\u05d0",
    "ramat gan", "\u05e8\u05de\u05ea \u05d2\u05df",
    "beer sheva", "be'er sheva", "\u05d1\u05d0\u05e8 \u05e9\u05d1\u05e2",
    "netanya", "\u05e0\u05ea\u05e0\u05d9\u05d4",
    "rehovot", "\u05e8\u05d7\u05d5\u05d1\u05d5\u05ea",
    "ness ziona", "\u05e0\u05e1 \u05e6\u05d9\u05d5\u05e0\u05d4",
    "rosh haayin", "\u05e8\u05d0\u05e9 \u05d4\u05e2\u05d9\u05df",
    "or yehuda", "\u05d0\u05d5\u05e8 \u05d9\u05d4\u05d5\u05d3\u05d4",
    "matam", "\u05de\u05ea\u05dd",
    "hod hasharon", "\u05d4\u05d5\u05d3 \u05d4\u05e9\u05e8\u05d5\u05df",
    "caesarea", "\u05e7\u05d9\u05e1\u05e8\u05d9\u05d4",
    "gedera", "\u05d2\u05d3\u05e8\u05d4",
]

EXCLUDED_LOCATION_KEYWORDS = [
    "haifa", "\u05d7\u05d9\u05e4\u05d4",
]

STUDENT_LEVEL_TITLE_KEYWORDS = [
    "student", "intern", "internship",
    "\u05e1\u05d8\u05d5\u05d3\u05e0\u05d8", "\u05e1\u05d8\u05d5\u05d3\u05e0\u05d8\u05d9\u05ea", "\u05de\u05ea\u05de\u05d7\u05d4",
    "working student", "part time", "part-time",
]

FIELD_RELEVANCE_KEYWORDS = [
    "chip design", "asic", "vlsi", "rtl", "verilog", "systemverilog",
    "soc", "silicon", "physical design", "digital design", "logic design",
    "place and route", "synthesis", "timing", "floorplan",
    "verification", "validation", "uvm", "test bench", "testbench", "formal",
    "analog", "mixed signal", "mixed-signal",
    "rf ", " rf", "rfic",
    "board design", "pcb", "layout",
    "hardware", "fpga", "embedded", "firmware",
    "circuit", "post silicon", "post-silicon",
    "low power", "power management", "dsp",
    "electrical engineer",
]

NEGATIVE_TITLE_KEYWORDS = [
    "senior", "principal", "staff", "lead ", " lead", "manager", "director",
    "vp ", "vice president", "head of", "chief",
    "expert",
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
