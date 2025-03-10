import re

# Copy of the patterns from the script
bedroom_patterns = [
    # Russian patterns
    r'(\d+)\s*(?:спальная|спальный|сп\.|спальни|спален)',  # Various forms of "bedroom"
    r'(\d+)\s*(?:спальн(?:ая|ый)|сп\.?\s*)?(?:квартира|дом|апартамент)',  # Apartment/house with bedrooms
    r'(?:квартира|дом|апартамент)\s*(?:с\s+)?(\d+)\s*(?:спальнями|спальней|спальнями)',  # "apartment with X bedrooms"
    # New Russian patterns
    r'(\d+)[\s\-]?комнатная',  # "1-комнатная квартира"
    r'(\d+)сп\b',  # "2сп" without space
    r'(?:спальни|спален|спальня)\s+(\d+)',  # "Спальни 2"
    r'(?:двумя|тремя|четырьмя)\s+спальн',  # Words "with two/three/four bedrooms"
    r'одной\s+спальн',  # "with one bedroom"
    r'с\s+(\d+)\s+спальн',  # "with X bedrooms"
    # Additional patterns for the failed test cases
    r'(\d+)\s+спальня\b',  # "1 спальня", "2 спальня"
    r'(\d+)\s+спальнями\b',  # "3 спальнями"
    # Additional patterns from the new examples
    r'спальни:\s*(\d+)',  # "Спальни: 1"
    r'(\d+)\s+сп-\s*ая',  # "2 сп- ая"
    r'(\d+)\s+спальные',  # "2 спальные"
    r'(\d+)\**\s+спальня',  # "1** спальня"
    r'(\d+)х\s*спальная',  # "3х спальная квартира"
    r'(\d+)\s+спальни\b',  # "3 спальни"
    # English patterns
    r'(\d+)\s*(?:bedroom|bed|br|b/r|b\.r\.|bdr)',  # Various abbreviations
    r'(\d+)\s*(?:-|\s+)?bed(?:room)?s?\b',  # Variations like "3-bed", "3 beds"
]

# Test cases - original examples
test_cases = [
    ('двумя спальнями', 2),
    ('1 спальня', 1),
    ('1-комнатная квартира', 1),
    ('двумя спальням', 2),
    ('3 спальнями', 3),
    ('Спальни 2', 2),
    ('2сп', 2),
    ('2 спальня', 2),
    # New examples
    ('Спальни: 1', 1),
    ('2 сп- ая', 2),
    ('3 спальни', 3),
    ('2 спальные', 2),
    ('1** спальня', 1),
    ('3х спальная квартира', 3)
]

def test_pattern(text):
    text_lower = text.lower()
    
    # Check for text-based matches
    if 'двумя' in text_lower and 'спальн' in text_lower:
        return 2
    elif 'тремя' in text_lower and 'спальн' in text_lower:
        return 3
    elif 'четырьмя' in text_lower and 'спальн' in text_lower:
        return 4
    elif 'одной' in text_lower and 'спальн' in text_lower:
        return 1
    
    # Check regex patterns
    for pattern in bedroom_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (IndexError, ValueError):
                # For patterns that don't have a group
                if 'студия' in text_lower or 'studio' in text_lower:
                    return 1
    return None

# Run the tests
print("Testing bedroom pattern detection:")
for text, expected in test_cases:
    result = test_pattern(text)
    status = 'PASS' if result == expected else 'FAIL'
    print(f'{status}: "{text}" -> Expected: {expected}, Got: {result}') 