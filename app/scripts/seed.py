#!/usr/bin/env python3
import asyncio
import os

async def main():
    print("🌱 Seeding database for PRODUCT_NAME...")
    # Add seeding logic here
    print("✅ Seeding complete.")

if __name__ == "__main__":
    if os.getenv("AUTO_SEED_DATA") == "true":
        asyncio.run(main())
