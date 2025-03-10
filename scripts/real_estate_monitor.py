#!/usr/bin/env python3
"""
Real Estate Telegram Monitor

This script monitors a real estate Telegram channel to:
1. Extract historical messages and parse property information
2. Store parsed data in CSV/JSON format
3. Listen for new messages and forward relevant ones to a private chat
4. Analyze price trends and statistics
"""

import os
import sys
import json
import csv
import re
import time
import asyncio
import getpass
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from telethon import TelegramClient, events, utils
from telethon.tl.types import Message
from telethon.errors import AuthRestartError, SessionPasswordNeededError
from dotenv import load_dotenv
from patterns import (
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
SOURCE_CHANNEL = os.getenv('TG_CHANNEL', '@Cyprus_Prop')

# Handle numeric chat IDs for target
target_chat_env = os.getenv('TG_TARGET', '')
if target_chat_env.lower() == 'self' or target_chat_env.lower() == 'me':
    TARGET_CHAT = 'me'  # Forward to "Saved Messages"
else:
    try:
        TARGET_CHAT = int(target_chat_env) if target_chat_env.isdigit() else target_chat_env
    except:
        TARGET_CHAT = target_chat_env

# Use the session name from .env if provided, otherwise use default
SESSION_NAME = os.getenv('TG_SESSION', 'real_estate_monitor')

# Storage paths
DATA_DIR = Path(__file__).parent / 'data'
RAW_MESSAGES_FILE = DATA_DIR / 'raw_messages.json'
PARSED_DATA_FILE = DATA_DIR / 'properties.csv'
LOGS_FILE = DATA_DIR / 'logs.txt'

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

def setup_logging():
    """Configure logging to file and console"""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOGS_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Ensure we use the same session file location for all operations
SESSION_PATH = Path(__file__).parent / f"{SESSION_NAME}.session"
if SESSION_PATH.exists():
    logger.info(f"Using existing session file: {SESSION_PATH}")

def normalize_price(price_str: str) -> Optional[float]:
    """Convert various price formats to a float value in euros"""
    if not price_str:
        return None
    # Remove commas and spaces
    price_str = re.sub(r'[,\s]', '', price_str)
    try:
        return float(price_str)
    except ValueError:
        return None

def convert_text_number(text):
    """Convert text-based numbers to digits."""
    text = text.lower()
    if re.search(r'(?i)студия|studio', text):
        return '0'
    elif re.search(r'(?i)одн|one|1', text):
        return '1'
    elif re.search(r'(?i)дву|two|2', text):
        return '2'
    elif re.search(r'(?i)тр[еи]|three|3', text):
        return '3'
    elif re.search(r'(?i)четыр|four|4', text):
        return '4'
    elif re.search(r'(?i)пят|five|5', text):
        return '5'
    elif re.search(r'(?i)шест|six|6', text):
        return '6'
    else:
        # Try to extract a number
        num_match = re.search(r'\d+', text)
        if num_match:
            return num_match.group(0)
    return text

def extract_field(text: str, patterns: List[str], group: int = 1) -> Optional[str]:
    """Extract field from text using a list of regex patterns"""
    if not text:
        return None
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return match.group(group)
            except IndexError:
                return match.group(0)
    return None

def clean_location(location):
    """Clean and normalize location string."""
    # Convert to lowercase for processing
    location = location.lower()
    
    # Remove leading/trailing special characters
    location = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', location)
    
    # Remove parentheses and their contents
    location = re.sub(r'\([^)]*\)', '', location)
    
    # Remove hashtags
    location = re.sub(r'#', '', location)
    
    # Normalize spaces and punctuation
    location = re.sub(r'[\s,]+', ' ', location)
    
    # Remove case endings for Russian locations
    location = re.sub(r'(?i)([лс])е$', r'\1', location)  # Remove "е" from "в Лимасоле", "в Пафосе"
    location = re.sub(r'(?i)и$', '', location)  # Remove "и" from "в Никосии"
    
    # Remove prepositions
    location = re.sub(r'(?i)^[вв]\s+', '', location)  # Remove "в" at start
    location = re.sub(r'(?i)^in\s+', '', location)  # Remove "in" at start
    
    # Remove common prefixes
    location = re.sub(r'(?i)^(?:расположен|находится|located|location|rent|аренда|продажа|sale)[\s:]+', '', location)
    
    # Remove common suffixes
    location = re.sub(r'(?i)[\s-]+(?:центр|center|centre)$', '', location)
    
    # Normalize city names
    location = re.sub(r'(?i)лимас+ол', 'лимассол', location)
    location = re.sub(r'(?i)limass?ol', 'limassol', location)
    location = re.sub(r'(?i)папх?ос', 'пафос', location)
    location = re.sub(r'(?i)paphos', 'pafos', location)
    location = re.sub(r'(?i)ларнак[аи]', 'ларнака', location)
    location = re.sub(r'(?i)larnaca', 'larnaka', location)
    location = re.sub(r'(?i)нико[сз]и[яи]', 'никосия', location)
    location = re.sub(r'(?i)nicosia', 'nikosia', location)
    
    # Normalize district names
    location = re.sub(r'(?i)герм?асо?[гй]е?[ий]?[ая]', 'гермасойя', location)
    location = re.sub(r'(?i)germas?o[gj]ei?[ay]s?', 'germasogeia', location)
    location = re.sub(r'(?i)[эе]рими', 'эрими', location)
    location = re.sub(r'(?i)erimi', 'erimi', location)
    location = re.sub(r'(?i)агиос[\s-]?афанасиос', 'агиос афанасиос', location)
    location = re.sub(r'(?i)agios[\s-]?athanasios', 'agios athanasios', location)
    location = re.sub(r'(?i)аг\.?\s?афанасиос', 'агиос афанасиос', location)
    location = re.sub(r'(?i)ag\.?\s?athanasios', 'agios athanasios', location)
    
    # Normalize case - capitalize first letter of each word
    location = ' '.join(word.capitalize() for word in location.split())
    
    return location.strip()

def parse_message(message_dict):
    """Parse a message dictionary and extract relevant information."""
    text = message_dict.get('message', '') if isinstance(message_dict, dict) else message_dict.message
    if not text:
        return None

    # Initialize property dictionary
    property_dict = {
        'raw_text': text,
        'price': None,
        'bedrooms': None,
        'location': None,
        'type': None,
        'date': message_dict.get('date') if isinstance(message_dict, dict) else message_dict.date,
        'message_id': message_dict.get('id') if isinstance(message_dict, dict) else message_dict.id,
        'link': message_dict.get('link') if isinstance(message_dict, dict) else None
    }

    logger.info("Starting to parse message:")
    logger.info(f"Raw text: {text}")

    # Extract price
    price_match = None
    for pattern in PRICE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            price_match = match
            logger.info(f"Found price match with pattern {pattern}: {match.group(0)}")
            break

    if price_match:
        price_str = price_match.group(1)
        # Remove any non-digit characters except decimal points
        price_str = re.sub(r'[^\d.]', '', price_str)
        try:
            property_dict['price'] = float(price_str)
            logger.info(f"Parsed price: {property_dict['price']}")
        except ValueError:
            logger.info(f"Failed to convert price string to float: {price_str}")
            pass
    else:
        logger.info("No price match found in patterns")

    # Extract bedrooms
    bedroom_match = None
    for pattern in BEDROOM_PATTERNS:
        match = re.search(pattern, text)
        if match:
            bedroom_match = match
            logger.info(f"Found bedroom match with pattern {pattern}: {match.group(0)}")
            break

    if bedroom_match:
        # Try to get the first group, if it exists, otherwise use the whole match
        bedroom_str = bedroom_match.group(1) if bedroom_match.groups() else bedroom_match.group(0)
        # Convert text numbers to digits if necessary
        bedroom_str = convert_text_number(bedroom_str)
        try:
            property_dict['bedrooms'] = int(bedroom_str)
            logger.info(f"Parsed bedrooms: {property_dict['bedrooms']}")
        except ValueError:
            logger.info(f"Failed to convert bedroom string to int: {bedroom_str}")
            pass
    else:
        logger.info("No bedroom match found in patterns")

    # Extract location
    location_matches = []
    for pattern in LOCATION_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Get the matched location and clean it
            location = clean_location(match.group(0))
            if location:  # Only add non-empty locations
                logger.info(f"Found location match with pattern {pattern}: {location}")
                # Check if this location contains both a city and a district
                has_city = any(city in location.lower() for city in ['лимассол', 'limassol', 'пафос', 'pafos', 'paphos', 'ларнака', 'larnaka', 'никосия', 'nikosia'])
                has_district = any(any(district in location.lower() for district in districts) for districts in DISTRICTS.values())
                
                # Prioritize locations that have both city and district
                if has_city and has_district:
                    location_matches.insert(0, location)
                else:
                    location_matches.append(location)

    if location_matches:
        # Take the first match (which will be a city+district match if we found one)
        property_dict['location'] = location_matches[0]
        logger.info(f"Selected location: {property_dict['location']}")
    else:
        logger.info("No location match found in patterns")

    # Extract property type
    type_match = None
    for pattern in TYPE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            type_match = pattern
            logger.info(f"Found type match with pattern {pattern}")
            break

    if type_match:
        property_dict['type'] = type_match

    logger.info(f"Final parsed data: {property_dict}")
    return property_dict

def save_messages(messages: List[Dict], output_file: str):
    """Save messages to JSON file"""
    def serialize_value(value):
        """Helper function to serialize values"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        elif isinstance(value, dict):
            return {k: serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [serialize_value(item) for item in value]
        return value

    # Convert messages to serializable format
    serializable_messages = []
    for msg in messages:
        msg_dict = {k: serialize_value(v) for k, v in msg.items()}
        serializable_messages.append(msg_dict)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_messages, f, ensure_ascii=False, indent=2)

def save_properties(properties: List[Dict], output_file: str):
    """Save properties to CSV file"""
    if not properties:
        return
    
    fieldnames = list(properties[0].keys())
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(properties)

def analyze_properties(properties_df=None):
    """Analyze property data and print statistics."""
    if properties_df is None:
        properties_df = pd.read_csv(PARSED_DATA_FILE)
    
    total_count = len(properties_df)
    price_count = properties_df['price'].notna().sum()
    bedroom_count = properties_df['bedrooms'].notna().sum()
    location_count = properties_df['location'].notna().sum()
    
    print("\nAnalysis Results:")
    print(f"Total properties: {total_count}")
    print(f"Properties with price: {price_count}")
    print(f"Properties with bedrooms: {bedroom_count}")
    print(f"Properties with location: {location_count}")
    print(f"Bedroom detection rate: {(bedroom_count/total_count)*100:.2f}%")
    print(f"Location detection rate: {(location_count/total_count)*100:.2f}%")
    
    # Count property types
    type_counts = properties_df['type'].value_counts()
    print("\nProperty Types:")
    for type_name, count in type_counts.items():
        print(f"{type_name}: {count}")
    
    # Price statistics
    if price_count > 0:
        print("\nPrice Statistics:")
        print(f"Mean price: €{properties_df['price'].mean():.2f}")
        print(f"Median price: €{properties_df['price'].median():.2f}")
    
    # Rental statistics by bedrooms
    if bedroom_count > 0:
        print("\nBedroom Statistics:")
        bedroom_stats = properties_df.groupby('bedrooms')['price'].agg(['count', 'mean', 'median']).round(2)
        for bedrooms, stats in bedroom_stats.iterrows():
            print(f"\n{bedrooms} bedroom(s):")
            print(f"Count: {stats['count']}")
            if stats['mean'] > 0:
                print(f"Mean price: €{stats['mean']:.2f}")
                print(f"Median price: €{stats['median']:.2f}")

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

async def monitor_messages(client: TelegramClient):
    """Monitor new messages and forward matching ones"""
    source_entity = await client.get_entity(SOURCE_CHANNEL)
    
    # Handle target chat ID
    try:
        if isinstance(TARGET_CHAT, int) or TARGET_CHAT.isdigit():
            target_id = int(TARGET_CHAT)
            try:
                target_entity = await client.get_entity(target_id)
            except ValueError:
                logger.info("Attempting to resolve target user through messages...")
                dialogs = await client.get_dialogs()
                target_entity = None
                for dialog in dialogs:
                    if dialog.entity and hasattr(dialog.entity, 'id') and dialog.entity.id == target_id:
                        target_entity = dialog.entity
                        break
                if not target_entity:
                    raise ValueError(f"Could not resolve target chat ID: {target_id}")
        else:
            target_entity = await client.get_entity(TARGET_CHAT)
            
        logger.info(f"Successfully resolved target chat: {utils.get_display_name(target_entity)}")
    except Exception as e:
        logger.error(f"Failed to resolve target chat: {e}")
        raise
    
    @client.on(events.NewMessage(chats=source_entity))
    async def handler(event):
        try:
            # Log raw message for debugging
            logger.info(f"Received message: {event.message.text[:200]}...")
            
            # Parse the message
            property_data = parse_message(event.message)
            if not property_data:
                logger.info("Skipping: Failed to parse property data")
                return
            
            # Debug log the parsed data
            logger.info(f"Parsed data: {property_data}")
            
            # Apply filters with null checks
            location = (property_data.get('location') or '').lower()
            if not ('limassol' in location or 'лимассол' in location):
                logger.info(f"Skipping: Location '{property_data.get('location')}' not in Limassol")
                return
                
            bedrooms = property_data.get('bedrooms', 0)
            if not bedrooms or bedrooms < 3:
                logger.info(f"Skipping: Bedrooms {bedrooms} < 3")
                return
                
            if property_data.get('type', None) == 'True':
                logger.info("Skipping: Property is for sale")
                return
                
            price = property_data.get('price')
            if not price:
                logger.info("Skipping: No price found")
                return
            if price > 3000:
                logger.info(f"Skipping: Price {price}€ > 3000€")
                return
            
            # Log that we found a match
            logger.info(f"Found matching property: {price}€, {bedrooms}bed in {location}")
            
            # Forward matching message with media
            try:
                # Forward the message with media
                forwarded = await client.forward_messages(target_entity, event.message)
                logger.info(f"Successfully forwarded message {event.message.id}")
                
                # Add a link to the original message
                channel_username = source_entity.username if hasattr(source_entity, 'username') else None
                if channel_username and forwarded:
                    link = f"https://t.me/{channel_username}/{event.message.id}"
                    await client.send_message(target_entity, f"Original post: {link}")
                    logger.info(f"Added link to original post: {link}")
                
            except Exception as e:
                logger.error(f"Failed to forward message: {e}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    logger.info(f"Started monitoring {SOURCE_CHANNEL} for new messages...")
    logger.info(f"Filtering for: Limassol, 3+ bedrooms, up to 3000€")
    logger.info(f"Forwarding to: {TARGET_CHAT}")
    
    try:
        # Keep the script running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring error: {e}")
        raise

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Real Estate Telegram Monitor')
    parser.add_argument('--fetch', action='store_true', help='Fetch messages from channel')
    parser.add_argument('--process', action='store_true', help='Process raw messages')
    parser.add_argument('--analyze', action='store_true', help='Analyze property data')
    parser.add_argument('--monitor', action='store_true', help='Monitor for new messages')
    parser.add_argument('--limit', type=int, default=1000, help='Number of messages to fetch')
    return parser.parse_args()

async def get_channel(client):
    """Get the channel entity."""
    channel = await client.get_entity(SOURCE_CHANNEL)
    logger.info(f"Connected to channel: {channel.title}")
    return channel

async def main():
    """Main function to run the real estate monitor."""
    args = parse_args()
    
    if args.monitor:
        client = await init_telegram()
        try:
            await monitor_messages(client)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        finally:
            await client.disconnect()
            logger.info("Disconnected from Telegram")
        return
    
    if args.fetch:
        # Initialize Telegram client
        client = await init_telegram()
        
        try:
            # Get channel entity
            channel = await get_channel(client)
            
            # Fetch messages
            messages = []
            async for message in client.iter_messages(channel, limit=args.limit):
                if message and message.message:  # Only process messages with text
                    message_dict = {
                        'message': message.message,
                        'date': message.date.isoformat() if message.date else None,
                        'id': message.id,
                        'link': f"https://t.me/c/{str(channel.id)[4:]}/{message.id}" if channel.id and message.id else None
                    }
                    messages.append(message_dict)
            
            # Save raw messages
            save_messages(messages, RAW_MESSAGES_FILE)
            logger.info(f"Saved {len(messages)} raw messages to {RAW_MESSAGES_FILE}")
            
        finally:
            # Disconnect from Telegram
            await client.disconnect()
            logger.info("Disconnected from Telegram")
    
    if args.process:
        # Load raw messages
        with open(RAW_MESSAGES_FILE, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        # Process messages
        properties = []
        for message in messages:
            property_data = parse_message(message)
            if property_data:
                properties.append(property_data)
        
        # Save processed properties
        properties_df = pd.DataFrame(properties)
        properties_df.to_csv(PARSED_DATA_FILE, index=False)
        logger.info(f"Saved {len(properties)} properties to {PARSED_DATA_FILE}")
    
    if args.analyze:
        analyze_properties()

if __name__ == '__main__':
    asyncio.run(main()) 