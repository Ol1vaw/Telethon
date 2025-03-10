"""
Real Estate Pattern Definitions

This module contains all regex patterns used for extracting information
from real estate listings in both Russian and English.
"""

PATTERNS = {
    'bedrooms': [
        # Russian patterns
        r'(\d+)\s*(?:спальная|спальный|сп\.|спальни|спален)',  # Various forms of "bedroom"
        r'(\d+)\s*(?:спальн(?:ая|ый)|сп\.?\s*)?(?:квартира|дом|апартамент)',  # Apartment/house with bedrooms
        r'(?:квартира|дом|апартамент)\s*(?:с\s+)?(\d+)\s*(?:спальнями|спальней|спальнями)',  # "apartment with X bedrooms"
        r'(\d+)[\s\-]?комнатная',  # "1-комнатная квартира"
        r'(\d+)сп\b',  # "2сп" without space
        r'(?:спальни|спален|спальня)\s+(\d+)',  # "Спальни 2"
        r'(?:двумя|тремя|четырьмя)\s+спальн',  # Words "with two/three/four bedrooms"
        r'одной\s+спальн',  # "with one bedroom"
        r'с\s+(\d+)\s+спальн',  # "with X bedrooms"
        r'(\d+)\s+спальня\b',  # "1 спальня", "2 спальня"
        r'(\d+)\s+спальнями\b',  # "3 спальнями"
        r'спальни:\s*(\d+)',  # "Спальни: 1"
        r'(\d+)\s+сп-\s*ая',  # "2 сп- ая"
        r'(\d+)\s+спальные',  # "2 спальные"
        r'(\d+)\**\s+спальня',  # "1** спальня"
        r'(\d+)х\s*спальная',  # "3х спальная квартира"
        r'(\d+)\s+спальни\b',  # "3 спальни"
        r'(\d+)-Х\s+СПАЛЬНАЯ',  # "3-Х СПАЛЬНАЯ ВИЛЛА"
        r'КОМНАТА\b',  # Single room listings
        r'(\d+)-сп\.',  # "4-сп." format
        r'(\d+)\s+cпальни\b',  # "2 cпальни" (lowercase 'c')
        r'(\d+)х\s+сп\b',  # "3х сп" format
        r'студия|studio',  # Studio apartments
        r'(\d+)-спал\.',  # "2-спал." format
        r'(\d+)-спальный',  # "4-спальный" format
        r'(\d+)\s+\**спальни',  # "3 **спальни" format
        r'(\d+)\s+сп\s+кв',  # "1 сп кв" format
        r'две\s+спальни',  # "две спальни" in Russian text
        r'(\d+)-спальн(?:ая|ый|ого)',  # "2-спальная", "3-спального дома"
        r'однокомнатную',  # "однокомнатную квартиру"
        r'вторая\s+спальня',  # "вторая спальня"
        r'третья\s+спальня',  # "третья спальня"
        r'четвертая\s+спальня',  # "четвертая спальня"
        r'пятая\s+спальня',  # "пятая спальня"
        r'зх\s*спальная',  # "зх спальная" (typo of "3х спальная")
        r'(?:одну?шк[ау]|однушк[ау])',  # "однушка", "однушку"
        r'просторн(?:ая|ую)\s+студию',  # "просторная студия", "просторную студию"
        r'(\d+)[\s\-]?(?:х|х\s+)?(?:ком|комн|комнаты?|комнатн)',  # Various forms of "комната"

        # English patterns
        r'(\d+)\s*(?:bedroom|bed|br|b/r|b\.r\.|bdr)',  # Various abbreviations
        r'(\d+)\s*(?:-|\s+)?bed(?:room)?s?\b',  # Variations like "3-bed", "3 beds"
        r'one\s+bed(?:room)?\b',  # "one bedroom"
        r'two\s+bed(?:room)?\b',  # "two bedrooms"
        r'three\s+bed(?:room)?\b',  # "three bedrooms"
        r'four\s+bed(?:room)?\b',  # "four bedrooms"
        r'five\s+bed(?:room)?\b',  # "five bedrooms"
        r'six\s+bed(?:room)?\b',  # "six bedrooms"
        r'(\d+).*bedrooms?\s+apartment',  # "two bedrooms apartment" with words in between
        r'(\d+)\s*bedrooms?\s+(?:apartment|flat|house)',  # "two bedrooms apartment"
        r'(?:amazing|spacious|luxury|new)\s+(\d+)\s*(?:bed|bedroom)',  # "amazing two bedrooms"
        r'(?:one|two|three|four|five|six)[\s\-](?:bed|bedroom)',  # "one-bed", "two bed"
    ],
    'location': [
        # Basic city patterns with flexible boundaries
        r'(?i)(?:^|[^\w]|#)(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w]|#)(?:ПАФОС|PAPHOS|Пафос|Paphos)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w]|#)(?:ЛАРНАКА|LARNACA|Ларнака|Larnaca)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w]|#)(?:НИКОСИЯ|NICOSIA|Никосия|Nicosia)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w]|#)(?:ПРОТАРАС|PROTARAS|Протарас|Protaras)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w]|#)(?:АЙЯ-НАПА|AYIA\s*NAPA|Айя-Напа|Ayia\s*Napa)(?:[^\w]|$)',

        # City with district patterns
        r'(?i)(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)[,\s]*[-–—]\s*([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',
        r'(?i)(?:ПАФОС|PAPHOS|Пафос|Paphos)[,\s]*[-–—]\s*([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',
        r'(?i)(?:ЛАРНАКА|LARNACA|Ларнака|Larnaca)[,\s]*[-–—]\s*([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',
        r'(?i)(?:НИКОСИЯ|NICOSIA|Никосия|Nicosia)[,\s]*[-–—]\s*([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',
        r'(?i)(?:ПРОТАРАС|PROTARAS|Протарас|Protaras)[,\s]*[-–—]\s*([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',
        r'(?i)(?:АЙЯ-НАПА|AYIA\s*NAPA|Айя-Напа|Ayia\s*Napa)[,\s]*[-–—]\s*([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',

        # City with district patterns using comma
        r'(?i)(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)[,\s]+([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',
        r'(?i)(?:ПАФОС|PAPHOS|Пафос|Paphos)[,\s]+([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',
        r'(?i)(?:ЛАРНАКА|LARNACA|Ларнака|Larnaca)[,\s]+([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',
        r'(?i)(?:НИКОСИЯ|NICOSIA|Никосия|Nicosia)[,\s]+([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',
        r'(?i)(?:ПРОТАРАС|PROTARAS|Протарас|Protaras)[,\s]+([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',
        r'(?i)(?:АЙЯ-НАПА|AYIA\s*NAPA|Айя-Напа|Ayia\s*Napa)[,\s]+([A-Za-zА-Яа-я\s]+?)(?:[^\w]|$)',

        # Location indicators with city
        r'(?i)(?:rent|аренда|location|расположение|📍)\s*[:-]?\s*(?:в\s+)?(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)(?:[^\w]|$)',
        r'(?i)(?:rent|аренда|location|расположение|📍)\s*[:-]?\s*(?:в\s+)?(?:ПАФОС|PAPHOS|Пафос|Paphos)(?:[^\w]|$)',
        r'(?i)(?:rent|аренда|location|расположение|📍)\s*[:-]?\s*(?:в\s+)?(?:ЛАРНАКА|LARNACA|Ларнака|Larnaca)(?:[^\w]|$)',
        r'(?i)(?:rent|аренда|location|расположение|📍)\s*[:-]?\s*(?:в\s+)?(?:НИКОСИЯ|NICOSIA|Никосия|Nicosia)(?:[^\w]|$)',
        r'(?i)(?:rent|аренда|location|расположение|📍)\s*[:-]?\s*(?:в\s+)?(?:ПРОТАРАС|PROTARAS|Протарас|Protaras)(?:[^\w]|$)',
        r'(?i)(?:rent|аренда|location|расположение|📍)\s*[:-]?\s*(?:в\s+)?(?:АЙЯ-НАПА|AYIA\s*NAPA|Айя-Напа|Ayia\s*Napa)(?:[^\w]|$)',

        # Hashtag patterns
        r'(?i)#(?:Аренда|Rent|Sale|Продажа)[^\n]*#(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)(?:[^\w]|$)',
        r'(?i)#(?:Аренда|Rent|Sale|Продажа)[^\n]*#(?:ПАФОС|PAPHOS|Пафос|Paphos)(?:[^\w]|$)',
        r'(?i)#(?:Аренда|Rent|Sale|Продажа)[^\n]*#(?:ЛАРНАКА|LARNACA|Ларнака|Larnaca)(?:[^\w]|$)',
        r'(?i)#(?:Аренда|Rent|Sale|Продажа)[^\n]*#(?:НИКОСИЯ|NICOSIA|Никосия|Nicosia)(?:[^\w]|$)',
        r'(?i)#(?:Аренда|Rent|Sale|Продажа)[^\n]*#(?:ПРОТАРАС|PROTARAS|Протарас|Protaras)(?:[^\w]|$)',
        r'(?i)#(?:Аренда|Rent|Sale|Продажа)[^\n]*#(?:АЙЯ-НАПА|AYIA\s*NAPA|Айя-Напа|Ayia\s*Napa)(?:[^\w]|$)',

        # Complex location formats
        r'(?i)(?:Колумбия|Columbia)[^\n]*(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)(?:[^\w]|$)',
        r'(?i)(?:Колумбия|Columbia)[^\n]*(?:ПАФОС|PAPHOS|Пафос|Paphos)(?:[^\w]|$)',
        r'(?i)(?:Колумбия|Columbia)[^\n]*(?:ЛАРНАКА|LARNACA|Ларнака|Larnaca)(?:[^\w]|$)',
        r'(?i)(?:Колумбия|Columbia)[^\n]*(?:НИКОСИЯ|NICOSIA|Никосия|Nicosia)(?:[^\w]|$)',
        r'(?i)(?:Колумбия|Columbia)[^\n]*(?:ПРОТАРАС|PROTARAS|Протарас|Protaras)(?:[^\w]|$)',
        r'(?i)(?:Колумбия|Columbia)[^\n]*(?:АЙЯ-НАПА|AYIA\s*NAPA|Айя-Напа|Ayia\s*Napa)(?:[^\w]|$)',

        # Common districts/areas
        r'(?i)(?:^|[^\w])(?:Mesa\s*Geitonia|Меса\s*Гитония|Меса\s*Гейтония)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Neapolis|Неаполис)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Germasogeia|Гермасогея|Гермасойя|Germasoya)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Potamos\s*Germasogeias|Потамос\s*Гермасогияс)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Athanasios|Айос\s*Атанасиос)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agia\s*Fyla|Агиа\s*Фила)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Zakaki|Закаки)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Tourist\s*Area|Туристическая\s*Зона|Турзона)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:City\s*Center|Центр|Старый\s*Город)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Mouttagiaka|Муттаяка|Мутаяка|Мутайяка)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Tychonas|Айос\s*Тихонас)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Katholiki|Католики)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agia\s*Napa|Агиа\s*Напа)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Pyrgos|Пиргос)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Ypsonas|Ипсонас)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Columbia|Колумбия)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Panthea|Пантея)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Polemidia|Полемидия)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Amathus|Аматус|Аматунта)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Pareklisia|Парклисия|Парекклисия)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Pissouri|Писсури)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Kato\s*Polemidia|Като\s*Полемидия)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Spyridonas|Айос\s*Спиридонас)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Omonia|Омония)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Pascucci|Паскуччи)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Ekali|Экали)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Tsirio|Тсирио)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Nikolaos|Айос\s*Николаос)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Georgios|Айос\s*Георгиос)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Ioannis|Айос\s*Иоаннис)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Andreas|Айос\s*Андреас)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Antonios|Айос\s*Антониос)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Nektarios|Айос\s*Нектариос)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Pavlos|Айос\s*Павлос)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agios\s*Theodoros|Айос\s*Теодорос)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agia\s*Barbara|Агиа\s*Варвара)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agia\s*Marina|Агиа\s*Марина)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agia\s*Triada|Агиа\s*Триада)(?:[^\w]|$)',
        r'(?i)(?:^|[^\w])(?:Agia\s*Zoni|Агиа\s*Зони)(?:[^\w]|$)',

        # Additional location patterns
        r'(?i)в\s+(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)е?',  # "в Лимасоле"
        r'(?i)в\s+(?:ПАФОС|PAPHOS|Пафос|Paphos)е?',
        r'(?i)в\s+(?:ЛАРНАКА|LARNACA|Ларнака|Larnaca)е?',
        r'(?i)в\s+(?:НИКОСИЯ|NICOSIA|Никосия|Nicosia)и?',
        r'(?i)в\s+(?:ПРОТАРАС|PROTARAS|Протарас|Protaras)е?',
        r'(?i)в\s+(?:АЙЯ-НАПА|AYIA\s*NAPA|Айя-Напа|Ayia\s*Napa)',

        # Location with property type
        r'(?i)квартира\s+в\s+(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)е?',
        r'(?i)дом\s+в\s+(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)е?',
        r'(?i)апартаменты?\s+в\s+(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)е?',
        r'(?i)студия\s+в\s+(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)е?',
        r'(?i)пентхаус\s+в\s+(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)е?',
        r'(?i)вилла\s+в\s+(?:ЛИМАСОЛ|LIMASSOL|Лимасол|Limassol)е?',

        # Location with property type (other cities)
        r'(?i)(?:квартира|дом|апартаменты?|студия|пентхаус|вилла)\s+в\s+(?:ПАФОС|PAPHOS|Пафос|Paphos)е?',
        r'(?i)(?:квартира|дом|апартаменты?|студия|пентхаус|вилла)\s+в\s+(?:ЛАРНАКА|LARNACA|Ларнака|Larnaca)е?',
        r'(?i)(?:квартира|дом|апартаменты?|студия|пентхаус|вилла)\s+в\s+(?:НИКОСИЯ|NICOSIA|Никосия|Nicosia)и?',
        r'(?i)(?:квартира|дом|апартаменты?|студия|пентхаус|вилла)\s+в\s+(?:ПРОТАРАС|PROTARAS|Протарас|Protaras)е?',
        r'(?i)(?:квартира|дом|апартаменты?|студия|пентхаус|вилла)\s+в\s+(?:АЙЯ-НАПА|AYIA\s*NAPA|Айя-Напа|Ayia\s*Napa)',
    ],
    'price': [
        r'(?:цена|price|стоимость|стоимостью)?[:\s]*[€₽$]?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:евро|euro|EUR)',
        r'(?:цена|price|стоимость|стоимостью)?[:\s]*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:евро|euro|EUR)',
        r'[€₽$]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'💶\s*(\d+)(?:€|евро|euro|EUR)?',  # New pattern for emoji euro symbol
    ],
    'is_sale': [
        r'#(?:продажа|sale|продам)',
        r'продается|for\s+sale',
        r'цена\s*:\s*.*\+ндс',
        r'продажа',
        r'sale price',
    ],
    'is_office': [
        r'(?:^|\s)офис\b',  # Office listings
        r'(?:^|\s)кабинет\b',  # Office/study room
        r'фитнес-зал',  # Gym
        r'участок',  # Land plot
        r'зем\.\s*уч\.',  # Land plot abbreviated
        r'видео\s+от',  # Video messages
        r'криптовалют',  # Cryptocurrency ads
        r'pintopay',  # Specific crypto ad
        r'ищем\s+арендаторов',  # Looking for tenants (commercial)
        r'ищу\s+(?:квартиру|дом)',  # Looking for apartment/house
        r'rent\s+new\s+flat',  # Generic rental requests
    ],
}

# Districts and areas
DISTRICTS = {
    'лимассол': [
        # Герасогея/Гермасойя variations
        r'герм?асо?[гй]е?[ий]?[ая]',
        r'germas?o[gj]ei?[ay]',
        r'germas?o[gj]i?[ay]s?',
        
        # Потамос Гермасогея
        r'потамос[\s-]?герм?асо?[гй]е?[ий]?[ая]',
        r'potamos[\s-]?germas?o[gj]ei?[ay]s?',
        
        # Эрими/Ерими
        r'[эе]рими',
        r'erimi',
        
        # Агиос Афанасиос
        r'агиос[\s-]?афанасиос',
        r'agios[\s-]?athanasios',
        r'аг\.?\s?афанасиос',
        r'ag\.?\s?athanasios',
        
        # Мони
        r'монi',
        r'moni',
        
        # Неаполис
        r'неаполис',
        r'neapolis',
        
        # Линопетра
        r'линопетра',
        r'linopetra',
        
        # Аматунта
        r'аматунта',
        r'amathounta',
        
        # Меса Гитония
        r'меса[\s-]?[гй]итон[ия]',
        r'mesa[\s-]?[gy]itonia',
        
        # Колумбия
        r'колумбия',
        r'columbia',
        
        # Центр
        r'центр',
        r'city[\s-]?cent[er]r?',
        
        # Епископи
        r'епископи',
        r'episkopi',
        
        # Апостолос
        r'апостолос',
        r'apostolos',
        
        # Патио
        r'патио',
        r'patio',
        
        # Потамос
        r'потамос',
        r'potamos',
        
        # Асоматос
        r'асомат?ос',
        r'asomatos',
        
        # Капсалос
        r'капсалос',
        r'kapsalos',
        
        # Закаки
        r'закаки',
        r'zakaki',
        
        # Омония
        r'омония',
        r'omonia',
        
        # Агия Фила
        r'агия[\s-]?фила',
        r'agia[\s-]?fyla',
        
        # Парклейн
        r'парклейн',
        r'parklane',
        
        # Молос
        r'молос',
        r'molos',
        
        # Полемидия
        r'полемидия',
        r'polemidia',
        
        # Агиос Николаос
        r'агиос[\s-]?николаос',
        r'agios[\s-]?nikolaos',
        r'аг\.?\s?николаос',
        r'ag\.?\s?nikolaos',
        
        # Агиос Тихонас
        r'агиос[\s-]?тихонас',
        r'agios[\s-]?tychonas',
        r'аг\.?\s?тихонас',
        r'ag\.?\s?tychonas',
        
        # Агиос Антониос
        r'агиос[\s-]?антониос',
        r'agios[\s-]?antonios',
        r'аг\.?\s?антониос',
        r'ag\.?\s?antonios',
        
        # Additional districts
        r'католики',
        r'katholiki',
        r'агиос[\s-]?иоанис',
        r'agios[\s-]?ioannis',
        r'петра[\s-]?и[\s-]?павла',
        r'petra[\s-]?i[\s-]?pavla',
        r'меза[\s-]?гетония',
        r'МЕЗА[\s-]?ГЕТОНИЯ',
        r'mesa[\s-]?getonia',
        r'MESA[\s-]?GETONIA',
        r'brain[\s-]?rocket',
        r'брейн[\s-]?рокет',
        r'мута[йя]ка',  # Add Мутаяка variant
        r'mutta[gy]iaka',
    ],
    'пафос': [
        # Като Пафос
        r'като[\s-]?пафос',
        r'kato[\s-]?paphos',
        
        # Университет
        r'универс?итет',
        r'university',
        
        # Молл
        r'молл',
        r'mall',
        
        # Kings Avenue
        r'kings[\s-]?avenue',
        r'кингс[\s-]?авеню',
        
        # Хлорака
        r'хлорака',
        r'chloraka',
        
        # Пейя
        r'пейя',
        r'peyia',
        
        # Корал Бей
        r'корал[\s-]?бей',
        r'coral[\s-]?bay',
        
        # Универсал
        r'универсал',
        r'universal',
        
        # Томбс оф Кингс
        r'томбс[\s-]?оф[\s-]?кингс',
        r'tombs[\s-]?of[\s-]?kings'
    ],
    'ларнака': [
        # Финикудес
        r'финикудес',
        r'finikoudes',
        
        # Дросия
        r'дрос[ия]',
        r'drosia',
        
        # Макензи
        r'макензи',
        r'mackenzie',
        
        # Ливадия
        r'ливадия',
        r'livadia',
        
        # Ороклини
        r'орокл?ини',
        r'oroklini',
        
        # Декелия
        r'декелия',
        r'dekelia',
        
        # Пила
        r'пила',
        r'pyla'
    ],
    'никосия': [
        # Энгоми
        r'энгоми',
        r'engomi',
        
        # Строволос
        r'строволос',
        r'strovolos',
        
        # Латсия
        r'латсия',
        r'latsia',
        
        # Акрополис
        r'акрополис',
        r'acropolis',
        
        # Макариос
        r'макариос',
        r'makarios',
        
        # Агландзия
        r'агландзия',
        r'aglantzia',
        
        # Палуриотисса
        r'палуриотисса',
        r'pallouriotissa'
    ]
}

# Update location patterns to include districts
LOCATION_PATTERNS = [
    # Basic city patterns with uppercase variations
    r'(?i)(?:^|\s|[^\w\s])(?:ЛИМАС+ОЛ|LIMASS?OL|ПАФОС|PAPHOS|ЛАРНАК[АИ]|LARNACA|НИКО[СЗ]И[ЯИ]|NICOSIA|ПРОТАРАС|PROTARAS|АЙ[ЯИ][\s-]?НАП[АЫ]|AY[IA][\s-]?NAPA)(?:$|\s|[^\w\s])',
    
    # District patterns with uppercase variations
    r'(?i)(?:^|\s|[^\w\s])(?:КАТОЛИКИ|KATHOLIKI|АГИОС[\s-]?ИОАНИС|AGIOS[\s-]?IOANNIS|ПЕТРА[\s-]?И[\s-]?ПАВЛА|PETRA[\s-]?I[\s-]?PAVLA|МЕЗА[\s-]?ГЕТОНИЯ|MESA[\s-]?GETONIA)(?:$|\s|[^\w\s])',
    
    # Location with property type (uppercase)
    r'(?i)(?:КВАРТИРА|ДОМ|АПАРТАМЕНТЫ?|СТУДИЯ|ПЕНТХАУС|ВИЛЛА)\s+(?:В|B)\s+(?:ЛИМАС+ОЛ|LIMASS?OL|ПАФОС|PAPHOS|ЛАРНАК[АИ]|LARNACA|НИКО[СЗ]И[ЯИ]|NICOSIA)(?:Е|E)?',
    
    # Street names and landmarks
    r'(?i)(?:^|\s|[^\w\s])(?:ПЕТРА[\s-]?И[\s-]?ПАВЛА|PETRA[\s-]?I[\s-]?PAVLA|BRAIN[\s-]?ROCKET|БРЕЙН[\s-]?РОКЕТ)(?:$|\s|[^\w\s])',
    
    # City with district format (with comma)
    r'(?i)(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia)[\s]*[,\-][\s]*(?:' + '|'.join([pattern for sublist in DISTRICTS.values() for pattern in sublist]) + r')',
    
    # City with district format (without comma)
    r'(?i)(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia)[\s]+(?:' + '|'.join([pattern for sublist in DISTRICTS.values() for pattern in sublist]) + r')',
    
    # District with city format (with comma)
    r'(?i)(?:' + '|'.join([pattern for sublist in DISTRICTS.values() for pattern in sublist]) + r')[\s]*[,\-][\s]*(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia)',
    
    # District with city format (without comma)
    r'(?i)(?:' + '|'.join([pattern for sublist in DISTRICTS.values() for pattern in sublist]) + r')[\s]+(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia)',
    
    # Standalone district patterns (only if we're confident about the city)
    r'(?i)(?:^|\s|[^\w\s])(?:' + '|'.join([pattern for sublist in DISTRICTS.values() for pattern in sublist]) + r')(?:$|\s|[^\w\s])',
    
    # Location indicators with city
    r'(?i)(?:расположен|находится|located|location|rent|аренда|продажа|sale)[\s:]+(?:[^\n]{0,30}?[\s,]+)?(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia|протарас|protaras|ай[яи][\s-]?нап[аы]|ay[ia][\s-]?napa)',
    
    # Hashtag patterns
    r'(?i)#(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia|протарас|protaras|ай[яи][\s-]?нап[аы]|ay[ia][\s-]?napa)',
    
    # Complex location formats
    r'(?i)(?:колумбия|columbia)[\s-]+(?:лимас+ол|limass?ol)',
    
    # Location after "в" (in)
    r'(?i)\s+[вВ]\s+(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia|протарас|protaras|ай[яи][\s-]?нап[аы]|ay[ia][\s-]?napa)',
    
    # Location after "in"
    r'(?i)\s+in\s+(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia|протарас|protaras|ай[яи][\s-]?нап[аы]|ay[ia][\s-]?napa)',
    
    # Location at start of line with comma
    r'(?i)^(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia|протарас|protaras|ай[яи][\s-]?нап[аы]|ay[ia][\s-]?napa)[\s]*[,\-]',
    
    # Location after newline
    r'(?i)\n(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia|протарас|protaras|ай[яи][\s-]?нап[аы]|ay[ia][\s-]?napa)[\s,]',
    
    # Location with district in parentheses
    r'(?i)(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia)[\s]*\((?:' + '|'.join([pattern for sublist in DISTRICTS.values() for pattern in sublist]) + r')\)',
    
    # District with city in parentheses
    r'(?i)(?:' + '|'.join([pattern for sublist in DISTRICTS.values() for pattern in sublist]) + r')[\s]*\((?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia)\)',
    
    # Location with district after colon
    r'(?i)(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia)[\s]*:[\s]*(?:' + '|'.join([pattern for sublist in DISTRICTS.values() for pattern in sublist]) + r')',
    
    # District with city after colon
    r'(?i)(?:' + '|'.join([pattern for sublist in DISTRICTS.values() for pattern in sublist]) + r')[\s]*:[\s]*(?:лимас+ол|limass?ol|пафос|paphos|ларнак[аи]|larnaca|нико[сз]и[яи]|nicosia)'
]

# Price patterns
PRICE_PATTERNS = [
    r'(?i)€\s*(\d+(?:[.,]\d+)?(?:\s*\d+)?)',  # Euro symbol followed by number
    r'(?i)(\d+(?:[.,]\d+)?(?:\s*\d+)?)\s*€',  # Number followed by Euro symbol
    r'(?i)цена:?\s*€?\s*(\d+(?:[.,]\d+)?(?:\s*\d+)?)',  # Price in Russian
    r'(?i)price:?\s*€?\s*(\d+(?:[.,]\d+)?(?:\s*\d+)?)',  # Price in English
    r'(?i)стоимость:?\s*€?\s*(\d+(?:[.,]\d+)?(?:\s*\d+)?)',  # Cost in Russian
    r'(?i)cost:?\s*€?\s*(\d+(?:[.,]\d+)?(?:\s*\d+)?)',  # Cost in English
    r'(?i)rent:?\s*€?\s*(\d+(?:[.,]\d+)?(?:\s*\d+)?)',  # Rent in English
    r'(?i)аренда:?\s*€?\s*(\d+(?:[.,]\d+)?(?:\s*\d+)?)',  # Rent in Russian
]

# Bedroom patterns
BEDROOM_PATTERNS = [
    r'(?i)(\d+)[\s-]*(?:сп?|к(?:омнат)?|bedroom|bed|br)',  # Number followed by bedroom indicators
    r'(?i)(?:студия|studio)',  # Studio apartment
    r'(?i)(?:одн|one|1)[\s-]*(?:сп?|к(?:омнат)?|bedroom|bed|br)',  # One bedroom
    r'(?i)(?:дву|two|2)[\s-]*(?:сп?|к(?:омнат)?|bedroom|bed|br)',  # Two bedrooms
    r'(?i)(?:тр[еи]|three|3)[\s-]*(?:сп?|к(?:омнат)?|bedroom|bed|br)',  # Three bedrooms
    r'(?i)(?:четыр|four|4)[\s-]*(?:сп?|к(?:омнат)?|bedroom|bed|br)',  # Four bedrooms
    r'(?i)(?:пят|five|5)[\s-]*(?:сп?|к(?:омнат)?|bedroom|bed|br)',  # Five bedrooms
    r'(?i)(?:шест|six|6)[\s-]*(?:сп?|к(?:омнат)?|bedroom|bed|br)',  # Six bedrooms
]

# Type patterns
TYPE_PATTERNS = [
    r'(?i)#(?:продажа|sale|продам)',  # Sale hashtags
    r'(?i)продажа',  # Sale in Russian
    r'(?i)продается|for\s+sale',  # For sale
] 