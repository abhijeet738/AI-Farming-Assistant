import asyncio
from app.core.supabase_client import get_supabase_client

async def main():
    client = get_supabase_client()
    try:
        # We need a token. We don't have one, but we can pass a garbage token and see the error.
        res = client.auth.get_user("garbage")
        print(res)
    except Exception as e:
        print("Error type:", type(e))
        print("Error message:", str(e))

asyncio.run(main())
