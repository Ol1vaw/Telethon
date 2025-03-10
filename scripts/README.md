# Real Estate Telegram Monitor

A Python script that monitors real estate listings in a Telegram channel, parses property information, and forwards relevant listings to a private chat.

## Features

- Extract property information from Telegram messages (price, bedrooms, location, etc.)
- Save historical messages for analysis
- Process and normalize the data for further analysis
- Forward matching properties to a private chat in real-time
- Analyze price trends and statistics

## Setup

1. Ensure you have Python 3.7+ installed
2. Install required packages:
   ```
   pip3 install telethon python-dotenv pandas
   ```
3. Configure the `.env` file with your Telegram credentials:
   ```
   TG_API_ID=your_api_id
   TG_API_HASH=your_api_hash
   TG_PHONE=your_phone_number
   TG_CHANNEL=@source_channel
   TG_TARGET=@target_chat
   ```
   Note: You can get API_ID and API_HASH from https://my.telegram.org

## Usage

The script can be run in different modes:

### Fetch Historical Messages

```bash
python3 real_estate_monitor.py --fetch --limit 2000
```

This will download the most recent 2000 messages from the source channel and save them as raw JSON.

### Process Messages

```bash
python3 real_estate_monitor.py --process
```

This will parse the raw messages and extract property information (price, bedrooms, location, etc.) into a structured CSV format.

### Analyze Data

```bash
python3 real_estate_monitor.py --analyze
```

This will analyze the parsed data and generate statistics like average prices by location and number of bedrooms.

### Real-Time Monitoring

```bash
python3 real_estate_monitor.py --listen
```

This will start monitoring the source channel in real-time, parse new messages, and forward relevant ones to your target chat.

## Multiple Operations

You can combine multiple operations in one command:

```bash
python3 real_estate_monitor.py --fetch --process --analyze
```

## Customizing Filters

You can specify filtering criteria directly via command line arguments:

```bash
# Filter by location, minimum bedrooms, and maximum price
python3 real_estate_monitor.py --listen --location Limassol --min-beds 2 --max-price 3000
```

Available filter options:
- `--location`: Filter by location name (e.g., Limassol, Paphos)
- `--min-beds`: Minimum number of bedrooms
- `--max-price`: Maximum price in euros

## Testing Forwarding

To test the forwarding functionality before starting the real-time listener, use the `--test-forward` option followed by the number of matching messages to forward:

```bash
# Forward up to 5 messages that match your criteria
python3 real_estate_monitor.py --test-forward 5 --location Limassol --min-beds 2 --max-price 3000
```

This will scan the most recent messages from the source channel and forward those that match your criteria to your target chat.

## Target Chat Configuration

You can configure where messages are forwarded to by setting the `TG_TARGET` variable in your `.env` file:

1. Forward to your own "Saved Messages": `TG_TARGET=me`
2. Forward to a chat by username: `TG_TARGET=username` (without @)
3. Forward to a chat by ID: `TG_TARGET=1234567890` (numeric ID)

If you're not sure what chats are available, run the `list_dialogs.py` helper script:

```bash
python3 list_dialogs.py
```

This will display all the chats you have access to, along with their types, names, and IDs.

## Data Storage

- Raw messages are stored in `data/raw_messages.json`
- Parsed property data is stored in `data/properties.csv`
- Logs are stored in `data/logs.txt` 