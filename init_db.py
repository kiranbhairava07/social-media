import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database import engine, Base, async_session_maker
from models import User, QRCode, QRScan
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_tables():
    """Create all tables in the database"""
    async with engine.begin() as conn:
        # Drop all tables (careful in production!)
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully")


async def create_default_user():
    """Create a default marketing user"""
    async with async_session_maker() as session:
        # Check if user already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "marketing@company.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if not existing_user:
            hashed_password = pwd_context.hash("marketing123")
            default_user = User(
                email="marketing@company.com",
                hashed_password=hashed_password
            )
            session.add(default_user)
            await session.commit()
            print("✅ Default user created:")
            print("   Email: marketing@company.com")
            print("   Password: marketing123")
        else:
            print("⚠️  Default user already exists")


async def create_sample_qr():
    """Create a sample QR code"""
    async with async_session_maker() as session:
        from sqlalchemy import select
        
        # Get the default user
        result = await session.execute(
            select(User).where(User.email == "marketing@company.com")
        )
        user = result.scalar_one()
        
        # Check if QR already exists
        result = await session.execute(
            select(QRCode).where(QRCode.code == "demo-2024")
        )
        existing_qr = result.scalar_one_or_none()
        
        if not existing_qr:
            sample_qr = QRCode(
                code="demo-2024",
                target_url="https://digital-links.vercel.app",
                created_by=user.id,
                is_active=True
            )
            session.add(sample_qr)
            await session.commit()
            print("✅ Sample QR code created: demo-2024")
        else:
            print("⚠️  Sample QR code already exists")


async def init_database():
    """Main initialization function"""
    print("🚀 Initializing database...")
    await create_tables()
    await create_default_user()
    await create_sample_qr()
    print("🎉 Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_database())