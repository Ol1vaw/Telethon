import re
import sys
import os
sys.path.append(os.path.abspath('scripts'))
from real_estate_monitor import PATTERNS, parse_message

# Examples provided by the user with expected bedroom counts
examples = [
    ('двумя спальнями', 2),
    ('1 спальня', 1),
    ('1-комнатная квартира', 1),
    ('двумя спальням', 2),
    ('3 спальнями', 3),
    ('Спальни 2', 2),
    ('2сп', 2),
    ('2 спальня', 2)
]

# Test each example
for text, expected in examples:
    # Create a test message
    test_message = {'id': 1, 'date': '2023-01-01', 'text': text}
    
    # Parse the message
    result = parse_message(test_message)
    
    # Check if the bedroom count matches
    actual = result['bedrooms']
    status = 'PASS' if actual == expected else 'FAIL'
    print(f'{status}: "{text}" -> Expected: {expected}, Got: {actual}') 