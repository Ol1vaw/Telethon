#!/usr/bin/env python3
"""
One-time run of the rental filter script with a specific time window
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
import logging

# Import from rental_filter.py
from rental_filter import (
    init_telegram, get_channel_entities, filter_and_forward_messages,
    filter_criteria, State, logger
)

async def run_once():
    """Run the filter once with a specific time window"""
    # Calculate time window from 13:47 until now
    now = datetime.now()
    start_time = datetime(now.year, now.month, now.day, 13, 47)
    hours_diff = (now - start_time).total_seconds() / 3600
    
    # Set the time window
    filter_criteria["time_period_hours"] = hours_diff
    
    logger.info(f"Running one-time filter with time window: {hours_diff:.2f} hours (from {start_time} to {now})")
    print(f"\nRunning one-time filter with time window: {hours_diff:.2f} hours")
    print(f"From: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"To:   {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize Telegram client
        client = await init_telegram()
        
        try:
            # Get channel entities
            source_entities, target_entity = await get_channel_entities(client)
            
            if not source_entities:
                logger.error("No source channels found")
                return
                
            if not target_entity:
                logger.error("No target channel found")
                return
            
            # Process and forward messages
            stats = await filter_and_forward_messages(client, source_entities, target_entity)
            
            # Log results
            if stats and stats.get('processed', 0) > 0:
                logger.info(f"Run completed successfully. Processed {stats['processed']} messages, "
                          f"forwarded {stats['forwarded']} matches.")
            else:
                logger.warning("No messages were processed in this run.")
            
        except Exception as e:
            logger.error(f"Error in processing: {e}")
        finally:
            # Disconnect the client
            await client.disconnect()
            logger.info("Disconnected from Telegram.")
        
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_once())
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1) 