# Telegram Rental Property Filter

A Python script that monitors Telegram channels for rental property listings and forwards matching ones based on user-defined criteria.

## Features

- Monitors specified Telegram channels for rental property listings
- Filters messages based on:
  - Price range
  - Location (city)
  - Number of bedrooms
  - Property type (apartments/offices)
  - Time period
- Forwards matching listings to a target channel
- Supports both direct message forwarding and link sharing
- Detailed statistics and analysis of processed messages

## Requirements

- Python 3.7+
- Telethon library
- python-dotenv

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd telegram-rental-filter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the `scripts` directory with your Telegram API credentials:
```
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_PHONE=your_phone_number
TG_CHANNEL=@source_channel
TG_TARGET=target_channel_id
TG_SESSION=session_name
```

## Usage

1. List available dialogs (optional):
```bash
python scripts/list_dialogs.py
```

2. Run the rental filter:
```bash
python scripts/rental_filter.py
```

The script will use predefined criteria for filtering messages. You can modify these criteria in the `filter_criteria` dictionary in `rental_filter.py`.

## Configuration

Default filtering criteria:
- Price: 1500€ - 3000€
- Location: Limassol
- Bedrooms: 3-10
- Property type: apartments
- Time period: Last 24 hours

## License

MIT License 