"""
app/utils/delivery_simulator.py
────────────────────────────────────────────────────────────────────
Generates a mock delivery order CSV from a random sample of existing
Sales records, then uploads it to a Supabase Storage bucket using
the official supabase-py client.

Required .env additions:
    SUPABASE_URL    = https://<project-ref>.supabase.co
    SUPABASE_KEY    = <service_role or anon key>
    SUPABASE_BUCKET = deliveries          # bucket name in Supabase Storage
"""

import csv
import io
import os
import random
import uuid
from datetime import date, timedelta

from dotenv import load_dotenv
from supabase import create_client, Client
from sqlalchemy.orm import Session

from .. import models

load_dotenv()

SUPABASE_URL    = os.environ["SUPABASE_URL"].strip().rstrip("/")
SUPABASE_KEY    = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "deliveries")


# ── Status distribution weights ───────────────────────────────────
#   new=15%  in-progress=25%  incomplete=10%  cancelled=5%  complete=45%
STATUS_CHOICES  = ["new", "in-progress", "incomplete", "cancelled", "complete"]
STATUS_WEIGHTS  = [15,     25,            10,            5,           45]


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def _tracking_number() -> str:
    """e.g. DLV-A3F9C2-20250515"""
    uid = uuid.uuid4().hex[:6].upper()
    return f"DLV-{uid}-{date.today().strftime('%Y%m%d')}"


def _delivery_dates(sale_date: date, status: str):
    """
    Returns (start_date, complete_date) based on status.

    - new           → start is null, complete is null
    - in-progress   → start assigned, complete is null
    - incomplete    → both assigned (complete ≤ today, but delivery failed)
    - cancelled     → both null
    - complete      → both assigned, complete ≥ start
    """
    if status in ("new", "cancelled"):
        return None, None

    start = sale_date + timedelta(days=random.randint(1, 3))

    if status == "in-progress":
        return start, None

    # incomplete or complete
    complete = start + timedelta(days=random.randint(1, 7))
    # cap complete date at today so we don't get future completions
    complete = min(complete, date.today())
    return start, complete


def _supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ─────────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────────
def generate_and_upload_deliveries(
    db: Session,
    sample_size: int   = 50,
    filename: str      = None,
) -> dict:
    """
    1. Pull a random sample of Sales records from the database.
    2. Generate one delivery order per sale.
    3. Write to an in-memory CSV.
    4. Upload the CSV to the configured Supabase S3 bucket.

    Returns a dict with metadata about the run.
    """

    # ── 1. Sample sales ──────────────────────────────────────────
    all_sales = db.query(models.Sales).all()
    if not all_sales:
        raise ValueError("No sales found in the database. Seed some sales first.")

    sample_size = min(sample_size, len(all_sales))
    sampled     = random.sample(all_sales, sample_size)

    # ── 2. Build delivery rows ───────────────────────────────────
    rows = []
    for sale in sampled:
        status               = random.choices(STATUS_CHOICES, STATUS_WEIGHTS)[0]
        start_dt, complete_dt = _delivery_dates(sale.sale_date, status)

        customer_name = (
            sale.customer.business_partner.name
            if sale.customer and sale.customer.business_partner
            else "Unknown"
        )

        rows.append({
            "tracking_number":        _tracking_number(),
            "sale_id":                sale.id,
            "customer_name":          customer_name,
            "sale_date":              sale.sale_date.isoformat(),
            "sale_amount":            str(sale.total_amount),
            "delivery_start_date":    start_dt.isoformat()    if start_dt    else "",
            "delivery_complete_date": complete_dt.isoformat() if complete_dt else "",
            "delivery_status":        status,
        })

    # ── 3. Write CSV to memory ───────────────────────────────────
    fieldnames = [
        "tracking_number",
        "sale_id",
        "customer_name",
        "sale_date",
        "sale_amount",
        "delivery_start_date",
        "delivery_complete_date",
        "delivery_status",
    ]

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    csv_bytes = buffer.getvalue().encode("utf-8")

    # ── 4. Upload via supabase-py ─────────────────────────────────
    if filename is None:
        filename = f"deliveries/deliveries_{date.today().isoformat()}_{uuid.uuid4().hex[:6]}.csv"

    client = _supabase_client()

    client.storage.from_(SUPABASE_BUCKET).upload(
        path         = filename,
        file         = csv_bytes,
        file_options = {"content-type": "text/csv", "upsert": "true"},
    )

    public_url = client.storage.from_(SUPABASE_BUCKET).get_public_url(filename)

    status_counts = {}
    for r in rows:
        status_counts[r["delivery_status"]] = status_counts.get(r["delivery_status"], 0) + 1

    return {
        "filename":      filename,
        "rows_generated": len(rows),
        "status_breakdown": status_counts,
        "bucket":        SUPABASE_BUCKET,
        "public_url":    public_url,
    }
