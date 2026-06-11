from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# ------------------ Connect to MongoDB ------------------
client = MongoClient("mongodb://localhost:27017/")  # or your Atlas URI
db = client["internship_portal"]  # Database name

# ------------------ Collections ------------------
internships_col = db["internships"]
profiles_col = db["profiles"]

# ------------------ Indexes ------------------
# Prevent duplicate internships
internships_col.create_index(
    [("title", 1), ("company", 1), ("location", 1)],
    unique=True
)
# For faster search by title or location
internships_col.create_index("title")
internships_col.create_index("location")

# Profiles: unique by name
profiles_col.create_index("name", unique=True)

# ------------------ Helper Functions ------------------
def insert_internship(job):
    """Insert internship, ignore duplicates"""
    try:
        internships_col.insert_one(job)
    except DuplicateKeyError:
        pass

def insert_profile(profile):
    """Insert user profile, ignore duplicates"""
    try:
        profiles_col.insert_one(profile)
    except DuplicateKeyError:
        pass

def get_internships(query=None, location=None, limit=50):
    """Fetch internships from DB, optional search by title and location"""
    db_query = {}
    if query:
        db_query["title"] = {"$regex": query, "$options": "i"}  # case-insensitive
    if location:
        db_query["location"] = {"$regex": location, "$options": "i"}
    return list(internships_col.find(db_query).limit(limit))

def get_profiles():
    """Fetch all profiles"""
    return list(profiles_col.find())