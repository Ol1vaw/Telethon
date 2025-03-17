# Rental Property Filter

This script filters and forwards rental property listings from Telegram channels based on user-specified criteria such as price range, location, bedrooms, and property type.

## Features

- **Automated Filtering**: Scans Telegram channels for rental property listings
- **Customizable Criteria**: Filter by price range, location, number of bedrooms, and property type
- **Smart Parsing**: Uses regex patterns to extract property details from unstructured text
- **Debug Channel**: Sends unparseable messages to a separate channel for review and improvement

## Setup

1. Create a `.env` file in the `scripts` directory with the following variables:

```
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_PHONE=your_phone_number
TG_CHANNELS=@channel1,@channel2
TG_TARGET=@your_target_channel
TG_DEBUG_CHANNEL=https://t.me/+RHVlh0Wnt3wwMzhi
```

2. Install the required dependencies:

```
pip install telethon python-dotenv
```

## Usage

Run the script with:

```
./scripts/new_rental_filter.py
```

The script will:
1. Connect to Telegram using your credentials
2. Scan the specified source channels for new messages
3. Parse messages to extract property details
4. Filter properties based on your criteria
5. Forward matching properties to your target channel
6. Send unparseable messages to your debug channel

## Debug Channel Feature

The debug channel feature helps improve the script's parsing capabilities by:

1. **Identifying Unparseable Messages**: Messages that look like rental listings but couldn't be fully parsed
2. **Providing Detailed Reports**: Each message includes information about what went wrong
3. **Creating a Learning Loop**: Review these messages to improve the regex patterns

### How to Use the Debug Channel

1. **Monitor the Debug Channel**: Check your debug channel after each run
2. **Identify Patterns**: Look for common formats that the parser couldn't handle
3. **Update Patterns**: Add new regex patterns to `patterns.py` files:
   - For price formats: `PRICE_PATTERNS`
   - For bedroom formats: `BEDROOM_PATTERNS`
   - For location formats: `LOCATION_PATTERNS`
4. **Test**: Run the script again to see if your new patterns worked

## Configuration

You can modify the following settings in the script:

- `TEST_MODE`: Set to `True` to run immediately instead of waiting for the next hour
- `LOOK_BACK_HOURS`: Number of hours to look back in test mode
- `MAX_UNPARSEABLE_QUEUE`: Maximum number of unparseable messages to store
- `filter_criteria`: Default filtering criteria for properties

## Troubleshooting

- **Database Locked Error**: Make sure no other instance of the script is running
- **Authentication Issues**: Check your API credentials in the `.env` file
- **Rate Limiting**: The script includes delays to avoid Telegram's rate limits

## Improving Pattern Matching

When you receive unparseable messages in your debug channel, look for:

1. **Missing Price Formats**: Add new patterns to `PRICE_PATTERNS` in `patterns.py`
2. **Missing Bedroom Formats**: Add new patterns to `BEDROOM_PATTERNS` in `patterns.py`
3. **Missing Location Formats**: Add new patterns to `LOCATION_PATTERNS` in `patterns.py`

Example pattern addition:

```python
# Add to patterns.py
PRICE_PATTERNS = [
    # Existing patterns...
    r'(?i)(\d+[\s,.]*\d*)\s*(?:€|EUR|euro)',  # New pattern
]
``` 