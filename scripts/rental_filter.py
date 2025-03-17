#!/usr/bin/env python3
"""
Rental Property Filter - Simplified Core Version

This script filters and forwards rental property listings from Telegram channels
based on user-specified criteria such as price range, location, bedrooms, and property type.
"""

import os
import sys
import re
import json
import time
import asyncio
import getpass
import logging
import pickle
import signal
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

from telethon import TelegramClient, events, utils
from telethon.tl.types import Message, Channel, User, PeerChannel
from telethon.errors import AuthRestartError, SessionPasswordNeededError
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Import pattern definitions
from patterns import (
    PATTERNS,
    PRICE_PATTERNS,
    BEDROOM_PATTERNS,
    LOCATION_PATTERNS,
    TYPE_PATTERNS,
    DISTRICTS
)

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Configuration values
API_ID = int(os.getenv('TG_API_ID', '0'))
API_HASH = os.getenv('TG_API_HASH', '')
PHONE = os.getenv('TG_PHONE', '')
SOURCE_CHANNELS = os.getenv('TG_CHANNELS', '@Cyprus_Prop').split(',')
TARGET_CHANNEL = os.getenv('TG_TARGET', '')
DEBUG_CHANNEL = os.getenv('TG_DEBUG_CHANNEL', '')  # Channel to send unparseable messages to

# Script name and state path
SCRIPT_NAME = "rental_filter"
STATE_PATH = os.path.join(os.path.dirname(__file__), f"{SCRIPT_NAME}_state.pkl")
SESSION_STRING_PATH = os.path.join(os.path.dirname(__file__), f"{SCRIPT_NAME}_session.txt")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"{SCRIPT_NAME}.log")
    ]
)
logger = logging.getLogger(__name__)

# User criteria
filter_criteria = {
    "min_price": 1500,
    "max_price": 3000,
    "city": "Limassol",
    "min_bedrooms": 3,
    "max_bedrooms": 10,
    "property_type": "apartments",  # "apartments" or "offices"
    "time_period_hours": 1,  # Default to 1 hour for regular runs
}

# Queue to store unparseable messages that might be rental listings
unparseable_messages = []
MAX_UNPARSEABLE_QUEUE = 50  # Maximum number of unparseable messages to store

def kill_existing_instances():
    """Kill any existing instances of this script"""
    current_pid = os.getpid()
    current_script = os.path.basename(__file__)
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if this is a Python process
            if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                cmdline = proc.info['cmdline']
                # Check if it's running our script
                if cmdline and any(current_script in cmd for cmd in cmdline):
                    # Don't kill ourselves
                    if proc.pid != current_pid:
                        logger.info(f"Killing existing instance (PID: {proc.pid})")
                        proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

class State:
    """Maintains the state between script runs"""
    def __init__(self):
        self.last_run = None
        self.load()
    
    def save(self):
        """Save state to file"""
        with open(STATE_PATH, 'wb') as f:
            pickle.dump({'last_run': self.last_run}, f)
        logger.info(f"Saved state: last_run = {self.last_run}")
    
    def load(self):
        """Load state from file"""
        try:
            with open(STATE_PATH, 'rb') as f:
                data = pickle.load(f)
                self.last_run = data.get('last_run')
                logger.info(f"Loaded state: last_run = {self.last_run}")
        except (FileNotFoundError, EOFError, pickle.PickleError) as e:
            logger.warning(f"Could not load state: {e}")
            self.last_run = None

def adjust_time_window(state: State) -> None:
    """Adjust the time window based on the last successful run"""
    now = datetime.now()
    
    if state.last_run:
        # Calculate hours since last successful run
        hours_since_last_run = (now - state.last_run).total_seconds() / 3600
        filter_criteria["time_period_hours"] = hours_since_last_run
        logger.info(f"Setting time window to {filter_criteria['time_period_hours']:.2f} hours (since last run at {state.last_run})")
    else:
        # If no last run, default to 24 hours
        filter_criteria["time_period_hours"] = 24
        logger.info(f"No previous run found. Setting time window to {filter_criteria['time_period_hours']} hours")

def extract_field(text, patterns):
    """Extract a field from text using a list of regex patterns"""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # If the pattern has a capture group, return the first group
            if match.groups():
                return match.group(1).strip()
            # Otherwise return the whole match
            return match.group(0).strip()
    return None

def convert_text_number(text):
    """Convert text representation of a number to an integer"""
    # Remove any non-numeric characters except for text numbers
    text = text.lower().strip()
    
    # Handle special cases for Russian/English text numbers
    if 'одн' in text or 'one' in text or 'single' in text:
        return 1
    elif 'дв' in text or 'two' in text:
        return 2
    elif 'тр' in text or 'three' in text:
        return 3
    elif 'четыр' in text or 'four' in text:
        return 4
    elif 'пят' in text or 'five' in text:
        return 5
    
    # Try to extract digits
    digits = re.search(r'(\d+)', text)
    if digits:
        return int(digits.group(1))
    
    # Default case
    return None

def clean_location(location):
    """Clean and normalize location strings"""
    if not location:
        return None
        
    # Convert to lowercase and remove extra whitespace
    location = location.lower().strip()
    
    # Remove common prefixes/suffixes
    location = re.sub(r'^(?:in|at|near|район|р-н|р-он|area)\s+', '', location, flags=re.IGNORECASE)
    
    # Map common variations
    location_map = {
        'лимассол': 'limassol',
        'лимасол': 'limassol',
        'лимассоле': 'limassol',
        'лимасоле': 'limassol',
        'лимассола': 'limassol',
        'лимасола': 'limassol',
        'никосия': 'nicosia',
        'никосии': 'nicosia',
        'ларнака': 'larnaca',
        'ларнаке': 'larnaca',
        'пафос': 'paphos',
        'пафосе': 'paphos',
        'протарас': 'protaras',
        'протарасе': 'protaras',
        'айя-напа': 'ayia napa',
        'айя напа': 'ayia napa',
    }
    
    # Check if the location is in our mapping
    for key, value in location_map.items():
        if key in location:
            return value
            
    return location

def parse_message(message) -> Dict[str, Any]:
    """Extract property data from a Telegram message"""
    global unparseable_messages
    
    if isinstance(message, Message):
        text = message.text or message.message or ""
        date = message.date
        message_id = message.id
        
        # Create a dict with message details
        message_dict = {
            'id': message_id,
            'text': text,
            'date': date.isoformat() if date else None,
        }
    else:
        # For direct text input
        text = message
        message_dict = {
            'text': text,
            'date': datetime.now().isoformat(),
        }
    
    # Initialize property dictionary
    property_dict = {
        'source': 'telegram',
        'message_id': message_dict.get('id'),
        'date': message_dict.get('date'),
        'location': None,
        'bedrooms': None,
        'price': None,
        'type': None,  # "apartments" or "offices"
        'parse_issues': []  # Track parsing issues for debugging
    }
    
    # Check if this might be a rental listing using simple heuristics
    likely_rental = False
    # Check for common rental-related terms
    rental_indicators = [
        r'(?i)rent', r'(?i)аренд', r'(?i)€\s*\d+', r'(?i)\d+\s*€', 
        r'(?i)bedroom', r'(?i)спальн', r'(?i)limassol', r'(?i)лимасол'
    ]
    
    for indicator in rental_indicators:
        if re.search(indicator, text):
            likely_rental = True
            break
    
    # Extract location
    location_match = extract_field(text, LOCATION_PATTERNS)
    if location_match:
        property_dict['location'] = clean_location(location_match)
        logger.debug(f"Parsed location: {property_dict['location']}")
    elif likely_rental:
        property_dict['parse_issues'].append("location_not_found")
    
    # Extract bedrooms
    bedroom_match = extract_field(text, BEDROOM_PATTERNS)
    if bedroom_match:
        logger.debug(f"Raw bedroom match: {bedroom_match}")
        try:
            bedroom_value = convert_text_number(bedroom_match)
            property_dict['bedrooms'] = bedroom_value
            logger.debug(f"Parsed bedrooms: {property_dict['bedrooms']}")
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing bedrooms '{bedroom_match}': {e}")
            property_dict['parse_issues'].append(f"bedroom_parse_error:{bedroom_match}")
    elif likely_rental:
        property_dict['parse_issues'].append("bedrooms_not_found")
    
    # Extract price
    price_match = None
    for pattern in PRICE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_match = match
            logger.debug(f"Found price match with pattern {pattern}: {match.group(0)}")
            break
    
    if price_match:
        try:
            # Try to get group 1 (the capture group with just the number)
            if len(price_match.groups()) > 0:
                price_str = price_match.group(1)
            else:
                # If no capture group, use the whole match
                price_str = price_match.group(0)
                # Try to extract just the digits
                price_str = re.sub(r'[^0-9.]', '', price_str)
            
            logger.debug(f"Raw price string: '{price_str}'")
            
            # Clean the price string
            price_str = re.sub(r'[^\d.]', '', price_str)
            # Convert to float
            property_dict['price'] = float(price_str)
            logger.debug(f"Parsed price: {property_dict['price']}")
        except (ValueError, TypeError, IndexError) as e:
            logger.error(f"Failed to convert price string to float: {price_str}, Error: {e}")
            property_dict['parse_issues'].append(f"price_parse_error:{price_str}")
    elif likely_rental:
        property_dict['parse_issues'].append("price_not_found")
    
    # Extract property type
    type_match = None
    for pattern in TYPE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            type_match = match
            break
    
    if type_match:
        type_text = type_match.group(0).lower()
        if any(word in type_text for word in ['офис', 'office', 'коммерческ']):
            property_dict['type'] = 'offices'
        else:
            property_dict['type'] = 'apartments'
    else:
        # Default to apartments if no type is specified
        property_dict['type'] = 'apartments'
    
    # Check if we have at least some data
    has_data = property_dict['location'] or property_dict['bedrooms'] or property_dict['price']
    
    # Check if this might be a rental listing but we couldn't parse it completely
    if likely_rental and (not has_data or len(property_dict['parse_issues']) > 0):
        # Only add if we have a real message (not direct text input)
        if isinstance(message, Message):
            issue_summary = ", ".join(property_dict['parse_issues']) if property_dict['parse_issues'] else "no_parseable_data"
            
            # Add some information about what we found or what's missing
            missing = []
            if not property_dict['location']: missing.append('location')
            if not property_dict['bedrooms']: missing.append('bedrooms')
            if not property_dict['price']: missing.append('price')
            
            # Create unparseable message entry
            unparseable_entry = {
                'message_id': message.id,
                'message_link': f"https://t.me/c/{str(message.chat_id)[4:]}/{message.id}" if message.chat_id else None,
                'date': message.date.isoformat() if message.date else None,
                'text': message.text,
                'issues': issue_summary,
                'missing': missing
            }
            
            # Add to unparseable messages queue
            unparseable_messages.append(unparseable_entry)
            
            # Keep queue size limited
            if len(unparseable_messages) > MAX_UNPARSEABLE_QUEUE:
                unparseable_messages.pop(0)  # Remove oldest
    
    return property_dict if has_data else None

def meets_criteria(property_data):
    """Check if a property meets the user's criteria"""
    # Price check
    price = property_data.get('price')
    if price is not None:
        if price < filter_criteria["min_price"] or price > filter_criteria["max_price"]:
            return False
    else:
        # Skip properties without price information
        return False
    
    # Location check
    location = (property_data.get('location') or '').lower()
    city = filter_criteria["city"].lower()
    
    # Map city variations
    city_variations = {
        'limassol': ['limassol', 'лимассол', 'лимасол', 'limass'],
        'paphos': ['paphos', 'пафос'],
        'larnaca': ['larnaca', 'ларнака'],
        'nicosia': ['nicosia', 'никосия'],
        'protaras': ['protaras', 'протарас'],
        'ayia napa': ['ayia napa', 'ayia-napa', 'айя-напа', 'айя напа']
    }
    
    # Check if any variation of the specified city is in the location string
    found_city = False
    if city:
        for key, variations in city_variations.items():
            if city in variations or city == key:
                # We found the correct key for this city
                if any(var in location for var in variations) or key in location:
                    found_city = True
                    break
        
        if not found_city:
            return False
    
    # Bedrooms check
    bedrooms = property_data.get('bedrooms')
    if bedrooms is not None:
        if bedrooms < filter_criteria["min_bedrooms"] or bedrooms > filter_criteria["max_bedrooms"]:
            return False
    
    # Property type check
    prop_type = property_data.get('type')
    if prop_type and filter_criteria["property_type"] != "any":
        if prop_type != filter_criteria["property_type"]:
            return False
    
    return True

async def init_telegram() -> TelegramClient:
    """Initialize and connect to Telegram with persistent authentication"""
    if not API_ID or not API_HASH:
        raise ValueError("API_ID and API_HASH must be set in .env file")

    # Try to load existing session string
    session_string = None
    try:
        if os.path.exists(SESSION_STRING_PATH):
            with open(SESSION_STRING_PATH, 'r') as f:
                session_string = f.read().strip()
                logger.info("Loaded existing session string")
    except Exception as e:
        logger.warning(f"Could not load session string: {e}")
        session_string = None

    # Create client with StringSession for persistence without SQLite
    client = TelegramClient(
        StringSession(session_string) if session_string else StringSession(),
        API_ID, 
        API_HASH
    )
    logger.info("Connecting to Telegram...")
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            if not PHONE:
                phone = input("Enter your phone number (international format): ")
            else:
                phone = PHONE
            
            logger.info("Sending authentication code...")
            await client.send_code_request(phone)
            code = input("Enter the verification code you received: ")
            
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = getpass.getpass("Enter your 2FA password: ")
                await client.sign_in(password=password)
            
            # Save the session string for future use
            session_str = client.session.save()
            try:
                with open(SESSION_STRING_PATH, 'w') as f:
                    f.write(session_str)
                logger.info("Saved session string for future authentication")
            except Exception as e:
                logger.error(f"Failed to save session string: {e}")
        
        logger.info("Successfully connected to Telegram!")
        return client
        
    except Exception as e:
        logger.error(f"Failed to connect to Telegram: {e}")
        if client:
            await client.disconnect()
        raise

async def get_channel_entities(client):
    """Get chat entities for source and target channels"""
    source_entities = []
    for channel in SOURCE_CHANNELS:
        try:
            entity = await client.get_entity(channel.strip())
            source_entities.append(entity)
            logger.info(f"Found source channel: {utils.get_display_name(entity)}")
        except Exception as e:
            logger.error(f"Error getting source channel {channel}: {e}")
    
    try:
        # Handle -100 prefix for channel IDs
        if TARGET_CHANNEL.lstrip('-').isdigit():
            # If it's a numeric ID, use it directly
            channel_id = int(TARGET_CHANNEL)
            # Use PeerChannel with the ID (removing -100 prefix if present)
            if str(channel_id).startswith('-100'):
                channel_id = int(str(channel_id)[4:])
            target_entity = await client.get_entity(PeerChannel(channel_id))
        else:
            target_entity = await client.get_entity(TARGET_CHANNEL)
            
        if target_entity:
            logger.info(f"Found target channel: {utils.get_display_name(target_entity)}")
    except Exception as e:
        logger.error(f"Error getting target channel {TARGET_CHANNEL}: {e}")
        target_entity = None
    
    return source_entities, target_entity

async def filter_and_forward_messages(client, source_entities, target_entity):
    """Filter messages from source channels and forward matches to target channel"""
    if not target_entity:
        logger.error("No target channel specified")
        return
        
    # Calculate the cutoff time
    now = datetime.now()
    cutoff_time = now - timedelta(hours=filter_criteria["time_period_hours"])
    
    print(f"\nTime window:")
    print(f"- Current time: {now}")
    print(f"- Cutoff time: {cutoff_time}")
    
    # Count statistics
    total_messages = 0
    processed_messages = 0
    messages_with_text = 0
    parseable_messages = 0
    matching_messages = 0
    forwarded_messages = 0
    
    print(f"\nAnalyzing and forwarding messages from the last {filter_criteria['time_period_hours']} hours...")
    print(f"Criteria: {filter_criteria['min_price']}€-{filter_criteria['max_price']}€, "
          f"{filter_criteria['min_bedrooms']}-{filter_criteria['max_bedrooms']} bedrooms, "
          f"in {filter_criteria['city']}")
    
    try:
        for source in source_entities:
            source_name = utils.get_display_name(source)
            print(f"\nProcessing messages from {source_name}...")
            
            try:
                async for message in client.iter_messages(source, reverse=False):
                    total_messages += 1
                    
                    # Track message time
                    message_date = message.date
                    if message_date.tzinfo:
                        message_date = message_date.replace(tzinfo=None)
                    
                    # Skip messages newer than now (shouldn't happen, but just in case)
                    if message_date > now:
                        continue
                        
                    # Skip messages older than cutoff time
                    if message_date < cutoff_time:
                        # Since messages are in reverse chronological order, 
                        # if we hit an old message we can break this channel's processing
                        break
                    
                    processed_messages += 1
                    
                    # Skip messages without text
                    if not message.text:
                        continue
                    
                    messages_with_text += 1
                    
                    # Parse the message
                    property_data = parse_message(message)
                    if not property_data:
                        continue
                    
                    parseable_messages += 1
                    
                    # Check if the property meets the criteria
                    if meets_criteria(property_data):
                        matching_messages += 1
                        # Log the match details
                        price = property_data.get('price', 'N/A')
                        bedrooms = property_data.get('bedrooms', 'N/A')
                        location = property_data.get('location', 'N/A')
                        print(f"Match found: {price}€, {bedrooms} bed in {location} (at {message_date})")
                        
                        try:
                            # Forward the original message with all media
                            await client.forward_messages(target_entity, message)
                            print(f"  ✓ Forwarded message to {utils.get_display_name(target_entity)}")
                            
                            forwarded_messages += 1
                            await asyncio.sleep(0.5)  # Small delay between forwards
                            
                        except Exception as e:
                            logger.error(f"Error forwarding message: {e}")
                            print(f"  ✗ Failed to forward message")
                    
                    # Print progress every 100 messages
                    if total_messages % 100 == 0:
                        print(f"Processed {total_messages} messages so far...")
                
                print(f"Finished processing messages from {source_name}.")
            
            except Exception as e:
                logger.error(f"Error processing messages from {source_name}: {e}")
                continue
        
        # Print summary
        print(f"\nSummary:")
        print(f"- Total messages scanned: {total_messages}")
        print(f"- Messages within time window: {processed_messages}")
        print(f"- Messages with text content: {messages_with_text}")
        print(f"- Messages with parseable property data: {parseable_messages}")
        print(f"- Messages matching all criteria: {matching_messages}")
        print(f"- Messages successfully forwarded: {forwarded_messages}")
        
        return {
            'total': total_messages,
            'processed': processed_messages,
            'with_text': messages_with_text,
            'parseable': parseable_messages,
            'matching': matching_messages,
            'forwarded': forwarded_messages
        }
    except Exception as e:
        logger.error(f"Error in filter_and_forward_messages: {e}")
        return None

async def send_unparseable_messages(client, target_entity):
    """Send unparseable messages to a debug channel for review"""
    global unparseable_messages
    
    if not target_entity or not unparseable_messages:
        return
    
    logger.info(f"Sending {len(unparseable_messages)} unparseable messages to debug channel")
    
    # Send a header message
    header = (
        "📋 **Unparsed Rental Messages Report**\n\n"
        f"The following {len(unparseable_messages)} messages couldn't be fully parsed "
        f"but might be rental listings. Review to improve pattern matching."
    )
    await client.send_message(target_entity, header)
    
    # Send each unparseable message with debug info
    for i, entry in enumerate(unparseable_messages, 1):
        try:
            debug_info = (
                f"🔍 **Unparsed Message #{i}**\n"
                f"Date: {entry['date']}\n"
                f"Issues: {entry['issues']}\n"
                f"Missing fields: {', '.join(entry['missing'])}\n\n"
                f"Original text:\n```\n{entry['text'][:500]}{'...' if len(entry['text']) > 500 else ''}\n```\n"
            )
            
            if entry['message_link']:
                debug_info += f"\nOriginal message: {entry['message_link']}"
            
            await client.send_message(target_entity, debug_info)
            await asyncio.sleep(0.5)  # Small delay to avoid rate limits
        except Exception as e:
            logger.error(f"Error sending unparseable message: {e}")
    
    # Clear the unparseable messages queue after sending
    unparseable_messages.clear()

async def send_statistics(client, target_entity, stats: Dict[str, int], time_window: float) -> None:
    """Send a statistics message to the target channel"""
    if not target_entity:
        return
        
    # Format the time window nicely
    if time_window < 1:
        time_str = f"{time_window * 60:.0f} minutes"
    else:
        time_str = f"{time_window:.1f} hours"
    
    # Create statistics message
    stats_message = (
        "📊 **Rental Search Statistics**\n\n"
        f"Time period: {time_str}\n"
        f"Criteria: {filter_criteria['min_price']}€-{filter_criteria['max_price']}€, "
        f"{filter_criteria['min_bedrooms']}-{filter_criteria['max_bedrooms']} bedrooms, "
        f"in {filter_criteria['city']}\n\n"
        f"🔍 Messages scanned: {stats['total']}\n"
        f"📅 Within time window: {stats['processed']}\n"
        f"📝 With text content: {stats['with_text']}\n"
        f"🏠 Property listings found: {stats['parseable']}\n"
        f"✅ Matching criteria: {stats['matching']}\n"
        f"📨 Successfully forwarded: {stats['forwarded']}\n\n"
        f"Next scan will start from: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    try:
        await client.send_message(target_entity, stats_message)
        logger.info("Sent statistics message to target channel")
    except Exception as e:
        logger.error(f"Failed to send statistics message: {e}")

async def main():
    """Main function"""
    # Kill any existing instances first
    kill_existing_instances()
    
    state = State()
    client = None

    try:
        # Try to load existing session string
        session_string = None
        try:
            if os.path.exists(SESSION_STRING_PATH):
                with open(SESSION_STRING_PATH, 'r') as f:
                    session_string = f.read().strip()
                    logger.info("Loaded existing session string")
        except Exception as e:
            logger.warning(f"Could not load session string: {e}")
            session_string = None

        # Initialize Telegram client with existing session if available
        client = TelegramClient(
            StringSession(session_string) if session_string else StringSession(),
            API_ID,
            API_HASH
        )
        
        logger.info("Connecting to Telegram...")
        await client.connect()
        
        if not await client.is_user_authorized():
            if not PHONE:
                phone = input("Enter your phone number (international format): ")
            else:
                phone = PHONE
            
            logger.info("Sending authentication code...")
            await client.send_code_request(phone)
            code = input("Enter the verification code you received: ")
            
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = getpass.getpass("Enter your 2FA password: ")
                await client.sign_in(password=password)
            
            # Save the session string for future use
            session_str = client.session.save()
            try:
                with open(SESSION_STRING_PATH, 'w') as f:
                    f.write(session_str)
                logger.info("Saved session string for future authentication")
            except Exception as e:
                logger.error(f"Failed to save session string: {e}")
        
        logger.info("Successfully connected to Telegram!")
        
        try:
            # Adjust time window based on last run
            adjust_time_window(state)
            
            # Get channel entities
            source_entities, target_entity = await get_channel_entities(client)
            
            if not source_entities:
                logger.error("No source channels found")
                return
                
            if not target_entity:
                logger.error("No target channel found")
                return
            
            # Initialize stats with zeros in case of failure
            stats = {
                'total': 0,
                'processed': 0,
                'with_text': 0,
                'parseable': 0,
                'matching': 0,
                'forwarded': 0
            }
            
            try:
                # Process and forward messages
                stats = await filter_and_forward_messages(client, source_entities, target_entity)
            except Exception as e:
                if "FLOOD_WAIT_" in str(e):
                    # Extract the wait time from the error message
                    wait_time = int(str(e).split("FLOOD_WAIT_")[1].split(" ")[0])
                    logger.warning(f"Hit Telegram rate limit. Need to wait {wait_time} seconds.")
                    print(f"\n⚠️ Hit Telegram rate limit. Waiting for {wait_time} seconds before continuing...")
                    
                    # Wait for the required time
                    await asyncio.sleep(wait_time)
                    
                    # Try again with a smaller batch
                    logger.info("Retrying with a smaller batch...")
                    stats = await filter_and_forward_messages(client, source_entities, target_entity)
                else:
                    # Re-raise other exceptions
                    raise
            
            # Send unparseable messages to debug channel if configured
            if DEBUG_CHANNEL and unparseable_messages:
                try:
                    debug_entity = await client.get_entity(DEBUG_CHANNEL)
                    if debug_entity:
                        await send_unparseable_messages(client, debug_entity)
                        logger.info(f"Sent {len(unparseable_messages)} unparseable messages to debug channel")
                    else:
                        logger.error(f"Could not find debug channel: {DEBUG_CHANNEL}")
                except Exception as e:
                    logger.error(f"Error sending unparseable messages: {e}")
            
            # Always send statistics message
            await send_statistics(client, target_entity, stats, filter_criteria["time_period_hours"])
            
            # Update state only if we successfully completed the run (even if no messages were processed)
            state.last_run = datetime.now()
            state.save()
            
            if stats.get('processed', 0) > 0:
                logger.info(f"Run completed successfully. Processed {stats['processed']} messages, "
                          f"forwarded {stats.get('forwarded', 0)} matches.")
            else:
                logger.info("Run completed successfully. No messages were processed in this run.")
            
        except Exception as e:
            logger.error(f"Error in processing: {e}")
            raise
        finally:
            # Always disconnect the client
            if client and client.is_connected():
                await client.disconnect()
                logger.info("Disconnected from Telegram.")
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        if client and client.is_connected():
            await client.disconnect()

if __name__ == "__main__":
    try:
        # Setup logging first
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(f"{SCRIPT_NAME}.log")
            ]
        )
        logger = logging.getLogger(__name__)
        
        # Load environment variables
        env_path = Path(__file__).parent / '.env'
        load_dotenv(env_path)
        
        # Run the main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Script terminated by user.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1) 