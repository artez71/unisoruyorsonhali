"""
Supabase Client Configuration
"""
import os
from supabase import create_client, Client
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Get Supabase client with anon key (for public operations)"""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

@lru_cache(maxsize=1)
def get_supabase_admin() -> Client:
    """Get Supabase admin client with service role key (bypasses RLS)"""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Initialize clients
supabase = get_supabase_client()
supabase_admin = get_supabase_admin()
