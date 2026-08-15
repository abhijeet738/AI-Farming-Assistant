import asyncio
from app.core.supabase_client import get_supabase_client
from app.core.security import _verify_supabase_jwt

async def main():
    client = get_supabase_client()
    # Use register instead
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    res = client.auth.sign_up({
        "email": email,
        "password": "password123"
    })
    token = res.session.access_token if res.session else None
    if not token:
        print("No token returned (email confirmation required?)")
        return
    
    print("Got token:", token[:20] + "...")
    try:
        payload = _verify_supabase_jwt(token)
        print("Verified payload:", payload)
    except Exception as e:
        print("Verification failed:", type(e).__name__, e)

asyncio.run(main())
