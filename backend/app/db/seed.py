"""
AIVOA — Minimal Seed Data

Inserts sample complaint records for manual testing and demo purposes.
Uses the example data from the architecture spec (§9).

Usage:
    cd backend
    python -m app.db.seed

Requires:
    - PostgreSQL running (docker-compose up -d)
    - Alembic migrations applied (alembic upgrade head)
"""

import asyncio
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.db.models import (
    Complaint,
    ComplaintStatus,
    DosageForm,
)


SEED_COMPLAINTS = [
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "complaint_number": "CC-2026-00001",
        "status": ComplaintStatus.pending_triage,
        "dosage_form": DosageForm.FDF,
        "complaint_source": "Email",
        "customer_name": "Apollo Pharmacy",
        "product_name": "Amoxicillin Capsules 500mg",
        "product_strength_grade": "500mg",
        "batch_lot_number": "AMX24601",
        "affected_quantity": None,
        "manufacturing_date": date(2026, 3, 12),
        "expiry_date": date(2028, 2, 28),
        "complaint_type": "Discoloration",
        "complaint_date": date(2026, 9, 14),
        "detailed_description": (
            "Apollo Pharmacy reported discolored capsules in "
            "Amoxicillin Capsules 500mg, batch AMX24601, "
            "manufactured 12 March 2026, expiring Feb 2028. "
            "Customer received via email on 14 September 2026."
        ),
        "raw_extraction_json": None,
    },
    {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "complaint_number": "CC-2026-00002",
        "status": ComplaintStatus.pending_triage,
        "dosage_form": DosageForm.API,
        "complaint_source": "Letter",
        "customer_name": "Zenith Life Sciences",
        "product_name": "Metformin Hydrochloride API",
        "product_strength_grade": "IP/BP grade",
        "batch_lot_number": "MET26-A01",
        "affected_quantity": "25 kg (1 HDPE Drum)",
        "manufacturing_date": date(2026, 1, 15),
        "expiry_date": date(2028, 1, 14),
        "complaint_type": "Foreign Matter Contamination",
        "complaint_date": date(2026, 9, 10),
        "detailed_description": (
            "Zenith Life Sciences reported foreign matter contamination "
            "in Metformin Hydrochloride API, IP/BP grade, batch MET26-A01. "
            "Black particulate matter observed in 25 kg HDPE drum "
            "received on 10 September 2026."
        ),
        "raw_extraction_json": None,
    },
]


async def seed():
    """Insert seed complaints if they don't already exist."""
    async with async_session_factory() as session:
        for data in SEED_COMPLAINTS:
            # Check if already seeded
            result = await session.execute(
                select(Complaint).where(Complaint.id == data["id"])
            )
            if result.scalar_one_or_none() is None:
                complaint = Complaint(**data)
                session.add(complaint)
                print(f"  [OK] Seeded: {data['complaint_number']}")
            else:
                print(f"  [--] Already exists: {data['complaint_number']}")

        await session.commit()

    # Dispose the engine to clean up connections
    await engine.dispose()
    print("\nSeed complete.")


if __name__ == "__main__":
    print("Seeding AIVOA database...\n")
    asyncio.run(seed())
