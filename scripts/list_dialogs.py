#!/usr/bin/env python3
"""
List available dialogs (chats, channels, users) that you have access to.
This helps identify what dialogs are available for forwarding messages.
"""

import os
import asyncio
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import AuthRestartError, SessionPasswordNeededError
from dotenv import load_dotenv
import getpass

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Get credentials from environment variables
API_ID = int(os.getenv('TG_API_ID', '0'))
API_HASH = os.getenv('TG_API_HASH', '')
PHONE = os.getenv('TG_PHONE', '')
SESSION_NAME = os.getenv('TG_SESSION', 'real_estate_monitor')

async def login(client):
    """Handle the login process"""
    try:
        if not await client.is_user_authorized():
            print("Starting login process...")
            
            await client.send_code_request(PHONE)
            code = input('Enter the code you received: ')
            
            try:
                await client.sign_in(PHONE, code)
            except SessionPasswordNeededError:
                password = getpass.getpass('Two-step verification enabled. Enter password: ')
                await client.sign_in(password=password)
        return True
            
    except Exception as e:
        print(f"Error during login: {e}")
        return False

async def list_dialogs():
    """List all available dialogs"""
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        # Connect to Telegram
        await client.connect()
        
        # Login
        if not await login(client):
            print("Login failed, exiting")
            return
        
        print("Login successful!")
        
        print("\nListing available dialogs (chats, channels, users):")
        print("-" * 70)
        print(f"{'ID':<15} {'Type':<10} {'Name':<30} {'Username'}")
        print("-" * 70)
        
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            # Determine entity type
            entity_type = type(entity).__name__
            
            # Get ID
            entity_id = entity.id
            
            # Get name
            name = getattr(entity, 'title', None) or getattr(entity, 'first_name', '')
            if hasattr(entity, 'last_name') and entity.last_name:
                name += f" {entity.last_name}"
            
            # Get username if available
            username = getattr(entity, 'username', None) or ''
            if username:
                username = f"@{username}"
            
            print(f"{entity_id:<15} {entity_type:<10} {name[:30]:<30} {username}")
        
        print("\nTo use one of these as a target, update the TG_TARGET in your .env file to:")
        print("1. For users/channels with username: Set TG_TARGET=username (without @)")
        print("2. For chats/channels without username: Set TG_TARGET=chat_id (the numeric ID)")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()
        print("\nDisconnected from Telegram")

if __name__ == "__main__":
    asyncio.run(list_dialogs()) 