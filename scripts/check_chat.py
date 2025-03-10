#!/usr/bin/env python3
"""
Check details about a specific chat ID to diagnose forwarding issues.
"""

import os
import asyncio
import sys
from pathlib import Path
from telethon import TelegramClient
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
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
SESSION_NAME = 'check_chat'

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

async def check_chat(chat_id):
    """Check details about a specific chat ID"""
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        # Connect to Telegram
        await client.connect()
        
        # Login
        if not await login(client):
            print("Login failed, exiting")
            return
        
        print("Login successful!")
        
        # Try different ways to access the chat
        print(f"\nChecking chat ID: {chat_id}")
        print("-" * 50)
        
        # Method 1: Direct ID
        print(f"Method 1: Trying to get entity by direct ID...")
        try:
            entity = await client.get_entity(int(chat_id))
            print(f"Success! Entity type: {type(entity).__name__}")
            print(f"Entity details: {entity}")
        except Exception as e:
            print(f"Failed: {e}")
        
        # Method 2: PeerUser
        print(f"\nMethod 2: Trying to get entity as PeerUser...")
        try:
            entity = await client.get_entity(PeerUser(int(chat_id)))
            print(f"Success! Entity type: {type(entity).__name__}")
            print(f"Entity details: {entity}")
        except Exception as e:
            print(f"Failed: {e}")
        
        # Method 3: PeerChat
        print(f"\nMethod 3: Trying to get entity as PeerChat...")
        try:
            entity = await client.get_entity(PeerChat(int(chat_id)))
            print(f"Success! Entity type: {type(entity).__name__}")
            print(f"Entity details: {entity}")
        except Exception as e:
            print(f"Failed: {e}")
        
        # Method 4: PeerChannel
        print(f"\nMethod 4: Trying to get entity as PeerChannel...")
        try:
            entity = await client.get_entity(PeerChannel(int(chat_id)))
            print(f"Success! Entity type: {type(entity).__name__}")
            print(f"Entity details: {entity}")
        except Exception as e:
            print(f"Failed: {e}")
        
        # Check if this chat is in the dialog list
        print("\nChecking if this chat is in your dialog list...")
        found = False
        async for dialog in client.iter_dialogs():
            if dialog.id == int(chat_id) or dialog.entity.id == int(chat_id):
                found = True
                print(f"Found in dialogs! Name: {dialog.name}, Type: {type(dialog.entity).__name__}")
                print(f"Dialog details: {dialog}")
                break
        
        if not found:
            print("This chat was not found in your dialog list.")
            print("This suggests you might not have access to this chat or it doesn't exist.")
        
        print("\nRecommendation:")
        if found:
            print("This chat exists and you have access to it. Try using a different format:")
            print(f"1. If it's a user chat, use TG_TARGET={chat_id}")
            print(f"2. If it's a group chat, try creating a new group and inviting yourself")
        else:
            print("1. Double-check the chat ID")
            print("2. Make sure you have access to this chat")
            print("3. Try using 'me' as the target to forward to your Saved Messages")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()
        print("\nDisconnected from Telegram")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_chat.py <chat_id>")
        sys.exit(1)
    
    chat_id = sys.argv[1]
    asyncio.run(check_chat(chat_id)) 