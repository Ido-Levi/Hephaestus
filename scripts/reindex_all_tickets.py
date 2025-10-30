#!/usr/bin/env python3
"""
Script to reindex all existing tickets in Qdrant.

This script regenerates embeddings for all tickets in the database
and stores them in Qdrant with the correct point ID format (UUID without "ticket-" prefix).
"""

import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import get_db, Ticket
from src.services.ticket_search_service import TicketSearchService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def reindex_all_tickets():
    """Reindex all tickets in the database."""

    # Get all ticket IDs and titles from database
    with get_db() as db:
        tickets = db.query(Ticket.id, Ticket.title).all()
        ticket_data = [(t.id, t.title) for t in tickets]
        ticket_count = len(ticket_data)

    logger.info(f"Found {ticket_count} tickets to reindex")

    if ticket_count == 0:
        logger.info("No tickets to reindex")
        return

    # Reindex each ticket
    success_count = 0
    fail_count = 0

    for idx, (ticket_id, ticket_title) in enumerate(ticket_data, 1):
        try:
            logger.info(f"[{idx}/{ticket_count}] Reindexing ticket {ticket_id}: {ticket_title[:50]}...")
            await TicketSearchService.reindex_ticket(ticket_id)
            success_count += 1
            logger.info(f"[{idx}/{ticket_count}] ✅ Successfully reindexed {ticket_id}")
        except Exception as e:
            fail_count += 1
            logger.error(f"[{idx}/{ticket_count}] ❌ Failed to reindex {ticket_id}: {e}")

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Reindexing Complete!")
    logger.info(f"{'='*60}")
    logger.info(f"Total tickets: {ticket_count}")
    logger.info(f"✅ Successfully reindexed: {success_count}")
    logger.info(f"❌ Failed: {fail_count}")
    logger.info(f"{'='*60}\n")

    if fail_count > 0:
        logger.warning(f"⚠️  {fail_count} tickets failed to reindex. Check logs above for details.")
        return 1
    else:
        logger.info("✅ All tickets successfully reindexed!")
        return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(reindex_all_tickets())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
