#!/usr/bin/env python3
"""
One-time script: Upload HANDBOOK_MAIN.md to OpenAI and create a vector store.
Run: python scripts/setup_knowledge_base.py
Then paste the printed VECTOR_STORE_ID into your .env file.
"""

import os
import time
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

HANDBOOK_PATH = Path(__file__).parent.parent / "HANDBOOK_MAIN_3.md"


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in environment or .env")
        sys.exit(1)

    if not HANDBOOK_PATH.exists():
        print(f"ERROR: Handbook not found at {HANDBOOK_PATH}")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print("Uploading HANDBOOK_MAIN (2).md...")
    with open(HANDBOOK_PATH, "rb") as f:
        uploaded = client.files.create(file=f, purpose="assistants")
    print(f"  File uploaded: {uploaded.id}")

    print("Creating vector store '30DLC_Handbook'...")
    vs = client.vector_stores.create(name="30DLC_Handbook")
    print(f"  Vector store created: {vs.id}")

    print("Adding file to vector store...")
    client.vector_stores.files.create(vector_store_id=vs.id, file_id=uploaded.id)

    print("Waiting for indexing to complete...")
    for attempt in range(30):
        vs_file = client.vector_stores.files.list(vector_store_id=vs.id).data
        if vs_file and vs_file[0].status == "completed":
            print("  Indexing complete!")
            break
        status = vs_file[0].status if vs_file else "pending"
        print(f"  Attempt {attempt + 1}: status={status} — waiting 5s...")
        time.sleep(5)
    else:
        print("WARNING: Timed out waiting for indexing. Check the OpenAI dashboard.")

    print()
    print("=" * 60)
    print(f"SUCCESS! Add this to your .env:")
    print(f"  VECTOR_STORE_ID={vs.id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
