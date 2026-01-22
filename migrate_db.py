import asyncio
from database import engine, Base

async def migrate_database():
    """
    Recreate tables with new schema.
    WARNING: This will delete all existing data!
    """
    print("🚀 Starting database migration...")
    print("⚠️  WARNING: This will delete all existing data!")
    
    confirm = input("Continue? (yes/no): ")
    if confirm.lower() != "yes":
        print("Migration cancelled")
        return
    
    async with engine.begin() as conn:
        # Drop all tables
        print("Dropping old tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        # Create new tables with updated schema
        print("Creating new tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database migration complete!")
    print("\n📝 Next steps:")
    print("1. Run: python init_db.py  (to create default user)")
    print("2. Restart your server")

if __name__ == "__main__":
    asyncio.run(migrate_database())