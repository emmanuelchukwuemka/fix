import random
import string
from datetime import datetime

def generate_referral_code(length=8):
    """Generate a unique referral code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_reward_code():
    """Generate a reward code: 5 uppercase letters + 3 digits"""
    letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(5))
    digits = ''.join(random.choice(string.digits) for _ in range(3))
    return letters + digits

def generate_batch_id():
    """Generate a batch ID for grouping reward codes"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_chars = ''.join(random.choice(string.ascii_uppercase) for _ in range(4))
    return f"BATCH-{timestamp}-{random_chars}"

def points_to_usd(points, rate=0.1):
    """Convert points to USD (default: 10 points = $1)"""
    return points * rate

def usd_to_points(usd, rate=0.1):
    """Convert USD to points (default: $1 = 10 points)"""
    return usd / rate

def get_tier_level(points):
    """Determine withdrawal tier based on points"""
    if points >= 15000:
        return "Platinum"
    elif points >= 8000:
        return "Gold"
    elif points >= 500:
        return "Silver"
    elif points >= 50:
        return "Bronze"
    else:
        return "None"

def get_tier_requirements(tier):
    """Get points required for a tier"""
    tiers = {
        "Bronze": 50,
        "Silver": 500,
        "Gold": 8000,
        "Platinum": 15000
    }
    return tiers.get(tier, 0)