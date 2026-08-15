import asyncio
from app.core.supabase_client import get_supabase_client
from app.config import settings

async def main():
    client = get_supabase_client()
    # We can't log in because of rate limits earlier, but wait, the rate limit was for sign up!
    # Let's try sign in with password
    try:
        res = client.auth.sign_in_with_password({
            "email": "baghiballia2004@gmail.com",
            "password": "password"  # I don't know the user's password, so this will fail.
        })
        print(res)
    except Exception as e:
        print(e)

asyncio.run(main())
