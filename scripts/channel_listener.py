#!/usr/bin/env python3
# A script to listen to Telegram channel messages and print them
import os
import sys
import time
import re
import getpass
from telethon import TelegramClient, events, utils
from telethon.errors import AuthRestartError, SessionPasswordNeededError
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
print(f"Looking for .env file at: {env_path}")
print(f"File exists: {env_path.exists()}")
load_dotenv(env_path)

# Get credentials from environment variables
API_ID = int(os.getenv('TG_API_ID', '24240188'))
API_HASH = os.getenv('TG_API_HASH', 'e9c2e002d538c39b3111c6767c979c0c')
PHONE = os.getenv('TG_PHONE', '+35799655967')
SOURCE_CHANNEL = '@Cyprus_Prop'
TARGET_CHANNEL = '@CY_props'  # Updated to use full channel name
SESSION = 'cyprus_prop_forwarder'

print("Configuration loaded:")
print(f"- Session name: {SESSION}")
print(f"- Source channel: {SOURCE_CHANNEL}")
print(f"- Target channel: {TARGET_CHANNEL}")
print(f"- Phone: {PHONE}")

def parse_message(text: str) -> dict:
    """Extract relevant information from message text"""
    info = {
        'bedrooms': None,
        'location': None,
        'raw_text': text
    }
    
    # Handle None or empty text
    if not text:
        return info
    
    # Extract number of bedrooms
    bedroom_patterns = [
        r'(\d+)\s*(?:bedroom|bed|br)',  # e.g., "3 bedroom" or "3 bed" or "3br"
        r'(\d+)[\s-]?б/к',  # Cyrillic variant
    ]
    for pattern in bedroom_patterns:
        if match := re.search(pattern, text.lower()):
            info['bedrooms'] = int(match.group(1))
            break
    
    # Check for Limassol
    limassol_patterns = ['limassol', 'лимассол', 'lemesos']
    if any(pattern in text.lower() for pattern in limassol_patterns):
        info['location'] = 'Limassol'
    
    return info

def matches_criteria(info: dict) -> bool:
    """Check if the parsed information matches our criteria"""
    return (info['bedrooms'] is not None and 
            info['bedrooms'] >= 3 and 
            info['location'] == 'Limassol')

async def process_messages(client):
    """Process last 1000 messages from the source channel"""
    print("\nFetching last 1000 messages...")
    
    try:
        print(f"Resolving source channel: {SOURCE_CHANNEL}")
        source_channel = await client.get_entity(SOURCE_CHANNEL)
        print(f"Source channel resolved: {utils.get_display_name(source_channel)}")
        
        print(f"\nResolving target channel: {TARGET_CHANNEL}")
        target_channel = await client.get_entity(TARGET_CHANNEL)
        print(f"Target channel resolved: {utils.get_display_name(target_channel)}")
        
    except ValueError as e:
        print(f"\nError: Could not find one of the channels. Please ensure:")
        print("1. You have joined both channels")
        print("2. The channel names are correct")
        print("3. You have permission to access both channels")
        print(f"\nError details: {e}")
        return
    except Exception as e:
        print(f"Error accessing channels: {e}")
        return
    
    messages_processed = 0
    messages_forwarded = 0
    
    try:
        print("\nStarting to process messages...")
        async for message in client.iter_messages(source_channel, limit=1000):
            messages_processed += 1
            
            if not message.text:
                continue
                
            info = parse_message(message.text)
            if matches_criteria(info):
                try:
                    await client.forward_messages(target_channel, message)
                    messages_forwarded += 1
                    print(f"\nForwarded message {message.id}:")
                    print(f"Bedrooms: {info['bedrooms']}")
                    print(f"Location: {info['location']}")
                    print(f"Text: {message.text[:200]}...")  # First 200 chars
                except Exception as e:
                    print(f"Error forwarding message {message.id}: {e}")
            
            if messages_processed % 100 == 0:
                print(f"Processed {messages_processed} messages, forwarded {messages_forwarded}")
        
        print(f"\nFinished processing {messages_processed} messages")
        print(f"Total messages forwarded: {messages_forwarded}")
    except Exception as e:
        print(f"Error processing messages: {e}")

async def login(client):
    """Handle the login process with retries"""
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        try:
            if not await client.is_user_authorized():
                print("Starting login process...")
                await client.send_code_request(PHONE)
                code = input('Enter the code you received: ')
                try:
                    await client.sign_in(PHONE, code)
                except SessionPasswordNeededError:
                    password = getpass.getpass('Two-step verification is enabled. Please enter your password: ')
                    await client.sign_in(password=password)
            return True
        except AuthRestartError:
            print("Auth restart required, trying again...")
            attempt += 1
            if attempt < max_attempts:
                print(f"Attempt {attempt + 1} of {max_attempts}")
                await client.disconnect()
                await client.connect()
            continue
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    print(f"Failed to login after {max_attempts} attempts")
    return False

async def main():
    print("\nInitializing Telegram client...")
    
    # Clean up any existing session
    session_file = Path(SESSION + '.session')
    if session_file.exists():
        try:
            session_file.unlink()
            print(f"Removed existing session file: {session_file}")
        except Exception as e:
            print(f"Warning: Could not remove session file: {e}")
    
    client = TelegramClient(SESSION, API_ID, API_HASH)
    
    try:
        print("Connecting to Telegram...")
        await client.connect()
        
        if await login(client):
            print("Login successful!")
            print("Connected successfully!")
            await process_messages(client)
        else:
            print("Login failed. Please try again later.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()
        print("\nDisconnected from Telegram")

# Start the client
if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 