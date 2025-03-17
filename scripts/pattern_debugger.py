#!/usr/bin/env python3
"""
Pattern Debugger for Rental Filter

This script analyzes messages from the last 24 hours and creates a detailed debug report
of messages that couldn't be parsed successfully. Use this to improve pattern matching.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from telethon import TelegramClient, utils
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Import parsing functions from rental filter
from rental_filter import (
    parse_message,
    SESSION_STRING_PATH,
    SOURCE_CHANNELS
)

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Configuration
API_ID = int(os.getenv('TG_API_ID', '0'))
API_HASH = os.getenv('TG_API_HASH', '')
DEBUG_OUTPUT = 'pattern_debug_report.txt'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DebugReport:
    def __init__(self):
        self.unparseable_messages: List[Dict[str, Any]] = []
        self.total_messages = 0
        self.messages_with_text = 0
        self.partially_parsed = 0
        self.fully_parsed = 0
        self.pattern_stats = {
            'location_not_found': 0,
            'price_not_found': 0,
            'bedrooms_not_found': 0,
            'price_parse_error': 0,
            'bedroom_parse_error': 0
        }
        
    def add_message(self, message_data: Dict[str, Any], parse_result: Optional[Dict[str, Any]]):
        """Add a message to the debug report"""
        self.total_messages += 1
        
        if not message_data.get('text'):
            return
            
        self.messages_with_text += 1
        
        if not parse_result:
            # Message couldn't be parsed at all
            self.unparseable_messages.append({
                'text': message_data['text'],
                'date': message_data['date'],
                'reason': 'no_parseable_data'
            })
            return
            
        # Check what was parsed successfully
        missing = []
        parse_issues = parse_result.get('parse_issues', [])
        
        if not parse_result.get('location'):
            missing.append('location')
            self.pattern_stats['location_not_found'] += 1
            
        if not parse_result.get('price'):
            missing.append('price')
            self.pattern_stats['price_not_found'] += 1
            
        if not parse_result.get('bedrooms'):
            missing.append('bedrooms')
            self.pattern_stats['bedrooms_not_found'] += 1
            
        for issue in parse_issues:
            if 'price_parse_error' in issue:
                self.pattern_stats['price_parse_error'] += 1
            if 'bedroom_parse_error' in issue:
                self.pattern_stats['bedroom_parse_error'] += 1
        
        if missing or parse_issues:
            self.partially_parsed += 1
            self.unparseable_messages.append({
                'text': message_data['text'],
                'date': message_data['date'],
                'missing_fields': missing,
                'parse_issues': parse_issues,
                'parsed_data': {
                    'location': parse_result.get('location'),
                    'price': parse_result.get('price'),
                    'bedrooms': parse_result.get('bedrooms'),
                    'type': parse_result.get('type')
                }
            })
        else:
            self.fully_parsed += 1

    def generate_report(self) -> str:
        """Generate a detailed debug report"""
        report = []
        report.append("=" * 80)
        report.append("RENTAL PROPERTY PATTERN DEBUG REPORT")
        report.append("=" * 80)
        report.append(f"\nGenerated at: {datetime.now()}")
        
        # Overall statistics
        report.append("\nOVERALL STATISTICS")
        report.append("-" * 50)
        report.append(f"Total messages analyzed: {self.total_messages}")
        report.append(f"Messages with text content: {self.messages_with_text}")
        report.append(f"Fully parsed messages: {self.fully_parsed}")
        report.append(f"Partially parsed messages: {self.partially_parsed}")
        report.append(f"Completely unparseable messages: {len([m for m in self.unparseable_messages if m.get('reason') == 'no_parseable_data'])}")
        
        # Pattern statistics
        report.append("\nPATTERN MATCHING STATISTICS")
        report.append("-" * 50)
        for pattern, count in self.pattern_stats.items():
            report.append(f"{pattern}: {count}")
        
        # Detailed message analysis
        report.append("\nDETAILED MESSAGE ANALYSIS")
        report.append("-" * 50)
        
        for idx, msg in enumerate(self.unparseable_messages, 1):
            report.append(f"\nMessage #{idx}")
            report.append(f"Date: {msg['date']}")
            
            if msg.get('reason') == 'no_parseable_data':
                report.append("Status: No parseable data found")
            else:
                report.append("Status: Partially parsed")
                report.append("Missing fields: " + ", ".join(msg.get('missing_fields', [])))
                report.append("Parse issues: " + ", ".join(msg.get('parse_issues', [])))
                
                if msg.get('parsed_data'):
                    report.append("Successfully parsed fields:")
                    for field, value in msg['parsed_data'].items():
                        if value is not None:
                            report.append(f"  {field}: {value}")
            
            report.append("\nMessage text:")
            report.append("-" * 20)
            report.append(msg['text'])
            report.append("-" * 20)
        
        # Pattern improvement suggestions
        report.append("\nPATTERN IMPROVEMENT SUGGESTIONS")
        report.append("-" * 50)
        
        if self.pattern_stats['location_not_found'] > 0:
            report.append("\nLocation patterns:")
            report.append("* Consider adding patterns for messages where location is mentioned as:")
            for msg in self.unparseable_messages:
                if 'location' in msg.get('missing_fields', []):
                    # Add first line of the message as an example
                    first_line = msg['text'].split('\n')[0][:100]
                    report.append(f"  - {first_line}")
        
        if self.pattern_stats['price_not_found'] > 0 or self.pattern_stats['price_parse_error'] > 0:
            report.append("\nPrice patterns:")
            report.append("* Review messages with price parsing issues:")
            for msg in self.unparseable_messages:
                if 'price' in msg.get('missing_fields', []) or any('price_parse_error' in issue for issue in msg.get('parse_issues', [])):
                    # Try to find price-like patterns in the text
                    price_lines = [line for line in msg['text'].split('\n') if '€' in line or 'eur' in line.lower()]
                    for line in price_lines[:3]:  # Show up to 3 examples
                        report.append(f"  - {line.strip()}")
        
        if self.pattern_stats['bedrooms_not_found'] > 0 or self.pattern_stats['bedroom_parse_error'] > 0:
            report.append("\nBedroom patterns:")
            report.append("* Review messages with bedroom parsing issues:")
            for msg in self.unparseable_messages:
                if 'bedrooms' in msg.get('missing_fields', []) or any('bedroom_parse_error' in issue for issue in msg.get('parse_issues', [])):
                    # Try to find bedroom-like patterns in the text
                    bed_lines = [line for line in msg['text'].split('\n') if any(term in line.lower() for term in ['bed', 'спал', 'комнат'])]
                    for line in bed_lines[:3]:  # Show up to 3 examples
                        report.append(f"  - {line.strip()}")
        
        return "\n".join(report)

async def analyze_messages(client: TelegramClient, hours: int = 24) -> None:
    """Analyze messages from the specified time period"""
    debug_report = DebugReport()
    
    # Calculate the cutoff time
    now = datetime.now()
    cutoff_time = now - timedelta(hours=hours)
    
    print(f"\nAnalyzing messages from: {cutoff_time}")
    print(f"                    to: {now}")
    print("\nThis may take a few minutes...\n")
    
    try:
        for channel in SOURCE_CHANNELS:
            try:
                entity = await client.get_entity(channel.strip())
                print(f"Processing channel: {utils.get_display_name(entity)}")
                
                async for message in client.iter_messages(entity, reverse=False):
                    # Skip messages outside our time window
                    message_date = message.date
                    if message_date.tzinfo:
                        message_date = message_date.replace(tzinfo=None)
                    
                    if message_date < cutoff_time:
                        continue
                    if message_date > now:
                        break
                    
                    # Prepare message data
                    message_data = {
                        'text': message.text or message.message or "",
                        'date': message_date.isoformat(),
                        'id': message.id
                    }
                    
                    # Try to parse the message
                    parse_result = parse_message(message)
                    
                    # Add to debug report
                    debug_report.add_message(message_data, parse_result)
                    
                    # Show progress
                    if debug_report.total_messages % 100 == 0:
                        print(f"Processed {debug_report.total_messages} messages...")
                
            except Exception as e:
                logger.error(f"Error processing channel {channel}: {e}")
                continue
        
        # Generate and save the report
        report = debug_report.generate_report()
        with open(DEBUG_OUTPUT, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nAnalysis complete!")
        print(f"Total messages analyzed: {debug_report.total_messages}")
        print(f"Messages with parsing issues: {len(debug_report.unparseable_messages)}")
        print(f"\nDetailed report saved to: {DEBUG_OUTPUT}")
        
    except Exception as e:
        logger.error(f"Error in analyze_messages: {e}")
        raise

async def main():
    """Main function"""
    try:
        # Try to load existing session
        session_string = None
        try:
            if os.path.exists(SESSION_STRING_PATH):
                with open(SESSION_STRING_PATH, 'r') as f:
                    session_string = f.read().strip()
                    logger.info("Loaded existing session string")
        except Exception as e:
            logger.warning(f"Could not load session string: {e}")
        
        if not session_string:
            logger.error("No session string found. Please run rental_filter.py first to authenticate.")
            return
        
        # Initialize client with existing session
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        
        print("Connecting to Telegram...")
        await client.connect()
        
        if not await client.is_user_authorized():
            logger.error("Session is invalid. Please run rental_filter.py first to authenticate.")
            return
        
        print("Successfully connected!")
        
        try:
            await analyze_messages(client)
        finally:
            await client.disconnect()
            
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 