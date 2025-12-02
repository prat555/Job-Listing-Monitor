# Configuration file for job searches

# Job search configurations
# Format: "search_term|location|sources"
# sources can be: indeed, linkedin (comma-separated)

SEARCHES = [
    {
        "search_term": "python developer",
        "location": "remote",
        "sources": ["indeed", "linkedin"],
        "max_pages": 5
    },
    {
        "search_term": "data scientist",
        "location": "remote",
        "sources": ["indeed"],
        "max_pages": 3
    },
    {
        "search_term": "software engineer",
        "location": "San Francisco",
        "sources": ["indeed", "linkedin"],
        "max_pages": 5
    }
]

# Keywords to filter/highlight (optional)
REQUIRED_KEYWORDS = [
    "python",
    "django",
    "flask",
    "fastapi",
    "machine learning",
    "data science"
]

# Keywords to exclude (optional)
EXCLUDED_KEYWORDS = [
    "senior only",
    "10+ years"
]
