import asyncio
from database import engine, Base

async def add_social_clicks_table():
    """
    Add the social_clicks table to the database.
    This script safely adds the new table without affecting existing data.
    """
    print("🚀 Adding social_clicks table...")
    
    async with engine.begin() as conn:
        # Only create the social_clicks table (won't affect existing tables)
        from models import SocialClick
        await conn.run_sync(SocialClick.__table__.create, checkfirst=True)
    
    print("✅ social_clicks table added successfully!")
    print("\n📊 You can now track social media platform clicks!")

if __name__ == "__main__":
    asyncio.run(add_social_clicks_table())