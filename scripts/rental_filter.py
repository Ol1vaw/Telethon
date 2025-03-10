#!/usr/bin/env python3
"""
Rental Property Filter

This script filters and forwards rental property listings from Telegram channels
based on user-specified criteria such as price range, location, bedrooms, and property type.

Usage:
    python rental_filter.py

The script will ask for the following filtering criteria:
- Minimum and maximum price
- City (e.g., Limassol, Paphos)
- Minimum and maximum bedrooms
- Property type (apartments or offices)
- Time period (in hours) to look back for messages

Matching messages will be forwarded to a specified target channel.
"""

import os
import sys
import re
import json
import time
import asyncio
import getpass
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

from telethon import TelegramClient, events, utils
from telethon.tl.types import Message, Channel, User
from telethon.errors import AuthRestartError, SessionPasswordNeededError
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

# Session name for this script
SESSION_NAME = "rental_filter"
SESSION_PATH = os.path.join(os.path.dirname(__file__), SESSION_NAME)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"{SESSION_NAME}.log")
    ]
)
logger = logging.getLogger(__name__)

# User criteria
filter_criteria = {
    "min_price": 0,
    "max_price": 10000,
    "city": "Limassol",
    "min_bedrooms": 0,
    "max_bedrooms": 10,
    "property_type": "apartments",  # "apartments" or "offices"
    "time_period_hours": 24,
}

def normalize_price(price_str: str) -> Optional[float]:
    """Convert various price formats to a float value in euros"""
    if not price_str:
        return None
    try:
        # Remove non-numeric characters except dots
        price_str = re.sub(r'[,\s]', '', price_str)
        # Convert to float
        return float(price_str)
    except (ValueError, TypeError):
        return None

def convert_text_number(text):
    """Convert textual numbers to digits (e.g., 'two' -> 2)"""
    text = text.lower()
    mapping = {
        'one': 1, 'два': 1, 'один': 1, 'одна': 1, 'one-bedroom': 1, 'однокомнатная': 1,
        'two': 2, 'две': 2, 'два': 2, 'two-bedroom': 2, 'двухкомнатная': 2,
        'three': 3, 'три': 3, 'three-bedroom': 3, 'трехкомнатная': 3,
        'four': 4, 'четыре': 4, 'four-bedroom': 4, 'четырехкомнатная': 4,
        'five': 5, 'пять': 5, 'five-bedroom': 5, 'пятикомнатная': 5,
        'six': 6, 'шесть': 6, 'six-bedroom': 6, 'шестикомнатная': 6,
        'studio': 0, 'студия': 0
    }
    
    for word, number in mapping.items():
        if word in text:
            return number
    
    try:
        return int(text)
    except (ValueError, TypeError):
        return None

def extract_field(text: str, patterns: List[str], group: int = 1) -> Optional[str]:
    """Extract a field from text using a list of regex patterns"""
    if not text:
        return None
        
    for pattern in patterns:
        try:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                # Try to get the specified group, fall back to group 0 if the group doesn't exist
                try:
                    return matches.group(group)
                except IndexError:
                    return matches.group(0)
        except Exception as e:
            # Just log the error and continue with next pattern
            logger.debug(f"Error with pattern {pattern}: {e}")
    
    # Fallback: simple search for city names
    city_keywords = [
        'limassol', 'лимассол', 'лимасол',
        'paphos', 'пафос', 
        'larnaca', 'ларнака',
        'nicosia', 'никосия',
        'protaras', 'протарас',
        'ayia napa', 'айя-напа', 'айя напа'
    ]
    
    text_lower = text.lower()
    for city in city_keywords:
        if city in text_lower:
            return city
    
    return None

def clean_location(location):
    """Clean and normalize location string"""
    if not location:
        return None
    
    # Map different spellings to standard names
    location_mapping = {
        'лимассол': 'Limassol',
        'limassol': 'Limassol',
        'лимасол': 'Limassol',
        'лимасcол': 'Limassol',
        'пафос': 'Paphos',
        'paphos': 'Paphos',
        'пафоc': 'Paphos',
        'ларнака': 'Larnaca',
        'larnaca': 'Larnaca',
        'ларнаца': 'Larnaca',
        'никосия': 'Nicosia',
        'nicosia': 'Nicosia',
        'никоcия': 'Nicosia',
        'протарас': 'Protaras',
        'protaras': 'Protaras',
        'протараc': 'Protaras',
        'айя-напа': 'Ayia Napa',
        'ayia napa': 'Ayia Napa',
        'айя напа': 'Ayia Napa',
        'айя-напa': 'Ayia Napa',
    }
    
    location = location.strip().lower()
    
    # Check if the location is a known city or matches a known mapping
    for key, value in location_mapping.items():
        if key in location:
            return value
    
    # Check if the location matches a district name
    for district in DISTRICTS:
        if district.lower() in location.lower():
            return district
    
    return location.capitalize()

def parse_message(message) -> Dict[str, Any]:
    """Extract property data from a Telegram message"""
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
    }
    
    # Extract location
    location_match = extract_field(text, LOCATION_PATTERNS)
    if location_match:
        property_dict['location'] = clean_location(location_match)
        logger.debug(f"Parsed location: {property_dict['location']}")
    
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
    
    # Extract price
    price_match = None
    for pattern in PRICE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_match = match
            logger.debug(f"Found price match with pattern {pattern}: {match.group(0)}")
            break
    
    if price_match:
        price_str = price_match.group(1)
        try:
            # Clean the price string
            price_str = re.sub(r'[^\d.]', '', price_str)
            # Convert to float
            property_dict['price'] = float(price_str)
            logger.debug(f"Parsed price: {property_dict['price']}")
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to convert price string to float: {price_str}")
    else:
        logger.debug("No price match found in patterns")
    
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
    
    return property_dict if has_data else None

async def init_telegram() -> TelegramClient:
    """Initialize and connect to Telegram"""
    if not API_ID or not API_HASH:
        raise ValueError("API_ID and API_HASH must be set in .env file")

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
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
                while True:
                    try:
                        password = getpass.getpass("Enter your 2FA password: ")
                        await client.sign_in(password=password)
                        break
                    except Exception as e:
                        logger.error(f"Authentication error: {e}")
                        retry = input("Would you like to try again? (y/n): ")
                        if retry.lower() != 'y':
                            raise
        
        logger.info("Successfully connected to Telegram!")
        return client
        
    except Exception as e:
        logger.error(f"Failed to connect to Telegram: {e}")
        await client.disconnect()
        raise

def get_user_criteria():
    """Get filtering criteria from user input"""
    print("\n=== Rental Property Filter ===")
    print("Using predefined criteria for testing:")
    
    # Predefined criteria for testing
    global filter_criteria
    filter_criteria = {
        "min_price": 1500,
        "max_price": 3000,
        "city": "Limassol",
        "min_bedrooms": 3,
        "max_bedrooms": 10,
        "property_type": "apartments",
        "time_period_hours": 24,
    }
    
    print("\nUsing these search criteria:")
    for key, value in filter_criteria.items():
        print(f"- {key}: {value}")

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
        # First try to find the target channel in dialogs
        target_entity = None
        async for dialog in client.iter_dialogs():
            if dialog.name == "CY props":
                target_entity = dialog.entity
                break
        
        if not target_entity:
            # If not found in dialogs, try direct resolution
            target_entity = await client.get_entity(TARGET_CHANNEL)
        
        if target_entity:
            logger.info(f"Found target channel: {utils.get_display_name(target_entity)}")
        else:
            logger.error("Could not find target channel in dialogs or by direct resolution")
            target_entity = None
            
    except Exception as e:
        logger.error(f"Error getting target channel {TARGET_CHANNEL}: {e}")
        target_entity = None
    
    return source_entities, target_entity

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

async def filter_and_forward_messages(client, source_entities, target_entity):
    """Filter messages from source channels and forward matches to target channel"""
    if not target_entity:
        logger.error("No target channel specified")
        return
        
    # Calculate the cutoff time
    now = datetime.now().replace(tzinfo=None)
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
    first_msg_time = None
    last_msg_time = None
    
    print(f"\nAnalyzing and forwarding messages from the last {filter_criteria['time_period_hours']} hours...")
    print(f"Criteria: {filter_criteria['min_price']}€-{filter_criteria['max_price']}€, "
          f"{filter_criteria['min_bedrooms']}-{filter_criteria['max_bedrooms']} bedrooms, "
          f"in {filter_criteria['city']}")
    
    for source in source_entities:
        source_name = utils.get_display_name(source)
        print(f"\nProcessing messages from {source_name}...")
        
        try:
            # Get messages without a limit, ordered by date (newest first)
            async for message in client.iter_messages(source, reverse=False):
                total_messages += 1
                
                # Track message time
                message_date = message.date
                if message_date.tzinfo:
                    message_date = message_date.replace(tzinfo=None)
                
                if not first_msg_time:
                    first_msg_time = message_date
                last_msg_time = message_date
                
                if message_date < cutoff_time:
                    # Since messages are ordered by date, we can break once we hit old messages
                    print(f"Reached messages older than {filter_criteria['time_period_hours']} hours, stopping scan...")
                    print(f"Last message time: {message_date}")
                    break
                
                processed_messages += 1
                
                # Show progress every 100 messages
                if processed_messages % 100 == 0:
                    print(f"Processed {processed_messages} messages... (Current message time: {message_date})")
                
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
                        # Get message link
                        message_link = f"https://t.me/{source.username}/{message.id}" if source.username else None
                        
                        if message_link:
                            # If we have a link, send it with the original text
                            text = f"{message.text}\n\nOriginal message: {message_link}"
                            await client.send_message(target_entity, text)
                            print(f"  ✓ Forwarded as link to {utils.get_display_name(target_entity)}")
                        else:
                            # If no link available, forward the original message with all media
                            await client.forward_messages(target_entity, message)
                            print(f"  ✓ Forwarded message to {utils.get_display_name(target_entity)}")
                        
                        forwarded_messages += 1
                        
                        # Add a small delay between forwards to avoid rate limits
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error forwarding message: {e}")
                        print(f"  ✗ Failed to forward message: {e}")
        
        except Exception as e:
            logger.error(f"Error processing messages from {source_name}: {e}")
    
    # Print detailed summary
    print(f"\nTime Range Analysis:")
    print(f"- First message time: {first_msg_time}")
    print(f"- Last message time: {last_msg_time}")
    if first_msg_time and last_msg_time:
        time_span = first_msg_time - last_msg_time
        print(f"- Time span: {time_span}")
    
    print(f"\nDetailed Analysis:")
    print(f"- Total messages scanned: {total_messages}")
    print(f"- Messages within last {filter_criteria['time_period_hours']} hours: {processed_messages}")
    print(f"- Messages with text content: {messages_with_text}")
    print(f"- Messages with parseable property data: {parseable_messages}")
    print(f"- Messages matching all criteria: {matching_messages}")
    print(f"- Messages successfully forwarded: {forwarded_messages}")
    
    if processed_messages > 0:
        match_rate = (matching_messages / processed_messages) * 100
        parse_rate = (parseable_messages / messages_with_text * 100) if messages_with_text > 0 else 0
        forward_rate = (forwarded_messages / matching_messages * 100) if matching_messages > 0 else 0
        print(f"\nAnalysis Rates:")
        print(f"- Parse rate: {parse_rate:.1f}% of messages with text could be parsed")
        print(f"- Match rate: {match_rate:.1f}% of messages within time period matched criteria")
        print(f"- Forward success rate: {forward_rate:.1f}% of matching messages were forwarded")
        print(f"- Messages per hour: {processed_messages / filter_criteria['time_period_hours']:.1f}")
    
    return {
        'total': total_messages,
        'processed': processed_messages,
        'with_text': messages_with_text,
        'parseable': parseable_messages,
        'matching': matching_messages,
        'forwarded': forwarded_messages,
        'time_span': time_span if first_msg_time and last_msg_time else None
    }

async def main():
    """Main function"""
    print("Welcome to the Rental Property Filter!")
    
    # Get user criteria
    get_user_criteria()
    
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
        await filter_and_forward_messages(client, source_entities, target_entity)
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
    finally:
        # Disconnect the client
        await client.disconnect()
        print("\nDisconnected from Telegram.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1) 