import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not url:
    raise RuntimeError("Missing SUPABASE_URL environment variable")

if not key:
    raise RuntimeError("Missing SUPABASE_KEY environment variable")

supabase: Client = create_client(url, key)