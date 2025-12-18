BASE_PROMPT = """
[Task]
Standardize NER expressions based on their mapped fields.
Always check the expression field before performing the standardization process below.

[Application Rules]
1. Apply standardization rules specific to each field type.
2. Maintain the order of the dictionary elements of the input list in the output list.
3. Only apply standardization to product_spec, product_price, and product_release_date fields. For all other fields (like product_model, product_option, product_code), keep them exactly as they are in the input without any modifications.
4. Do not apply any changes to expressions that are not spec, price, or product_release_date. Namely do not apply any changes to product_model or product_code.
5. Preserve the order of the objects of the input list in the output list.
6. The number of objects in the input must be preserved in the output.
    - If 6 items were given, 6 items should be returned. NEVER return less or more than the input items.
    - ALL input objects must appear in the output, regardless of their field type.
    - Objects with non-target fields (not product_spec, product_price, or product_release_date) should remain completely unchanged.
7. Do not apply date changes to 'promotion_date' or 'user_action_date' fields, only apply to 'product_release_date'.

[Output Format]
- Return ALL input objects with standardized expressions only for product_spec, product_price, and product_release_date fields.
- Objects with other field types (product_model, product_option, product_code, etc.) must remain exactly as provided in the input.
- The output must contain the exact same number of objects as the input.
[
    {
        "expression": "Standardized Expression",
        "field": "Field Name",  // unchanged
        "operator": "Operator"  // unchanged
    },
    ... // additional items
]
"""

VALIDATION_PROMPT = """
[Validation Process]
Before outputting each entity, verify:
1. Is the standardization rule for the field type applied correctly?
2. Is the numerical value properly standardized to remove spaces and commas?
3. Is there an unnecessary space in the expression between the numbers for product_spec and product_price? If yes, remove the blank space to make the number into an integer value (like '3 300' to '3300')
4. is the standardization applied to only the product_spec, product_price, and product_release_date fields?
5. Is the order of the objects of the input maintained in the output list?
6. Are ALL objects preserved in the output? 
   - The output list must have the same length as the input list
   - Never remove or skip any input items
"""

MODULE_PROMPTS = {
    "product_spec_module": {
        "KR": """
[Product Spec Standardization]
- For product_spec field expressions, apply the following tasks in sequence:

Task 1: Add a space between numerical values and unit expressions
- Example: '3cm' → '3 CM', '10kg' → '10 KG'

Task 2: Remove blank spaces and commas from numerical values
    - Convert all numbers by removing commas and spaces BETWEEN digits
    - Examples: '3,300W' → '3300 W', '7,200W' → '7200 W'
    - KEEP exactly ONE space between the number and the unit

Task 3: Standardize unit expressions to English (APPLY FOR ONLY THE BELOW)
    - Length:
        Meter: 'M'
        Kilometer: 'KM'
        Centimeter: 'CM'
        Millimeter: 'MM'
        Inch: 'INCH'
        Foot: 'FT'
        Yard: 'YD'
        Mile: 'MI'
        * Example: '80인치' → '80 INCH', '5미터' → '5 M', '500리터대' → '500 L'
    - Weight:
        Kilogram: 'KG'
        Gram: 'G'
        Ton: 'T'
        Pound: 'LB'
        Ounce: 'OZ'
        * Example: '10킬로' → '10 KG', '500그램' → '500 G'
    - Storage:
        Kilobyte: 'KB'
        Megabyte: 'MB'
        Gigabyte: 'GB'
        Terabyte: 'TB'
        * Example: '256기가' → '256 GB', '1테라' → '1 TB'
    - Power:
        Watt: 'W'
        Kilowatt: 'KW'
        mAmpere: 'MAH'
        WattHour: 'WH'
        Volt: 'V'
        * Example: '100와트' → '100 W', 5000밀리암페어' → '5000 MAH''
    - Capacity:
        Liter: 'L'
        Milliliter: 'ML'
        Gallon: 'GAL'
        Square Meter: 'M²'
        Square Centimeter: 'CM²'
        Square Inch: 'INCH²'
        Sqaure Foot: 'FT²'
        * Example: '90제곱미터' → '90 M²', '30제곱센치' → '5 CM²'
   - This task is only applied if the expression is NOT in the exceptions list
   - Always apply standardization for Length, Weight, Storage

[Exceptions for Product Spec]
- Apply ONLY Task 1 (adding space) for:
    - '구' as in '3구' → '3 구'
    - '인용' as in '10인용' → '10 인용'
    - '등급' as in '1등급' → '1 등급'
    - '채널' as in "5.1채널" → '5.1 채널'
    - '평' as in "20평" → '20 평'
- When there are multiple numbers for the same unit, keep all numbers together and do not remove the divider
    - Example: '25/22kg' → '25/22 KG'
""",
        "GB": """
[Product Spec Standardization]
- For product_spec field expressions, apply the following tasks in sequence:

Task 1: Add a space between numerical values and unit expressions
- Example: '3cm' → '3 CM', '10kg' → '10 KG'

Task 2: Remove blank spaces and commas from numerical values
    - Convert all numbers by removing commas and spaces BETWEEN digits
    - Examples: '3,300W' → '3300 W', '7,200W' → '7200 W'
    - KEEP exactly ONE space between the number and the unit

Task 3: Standardize unit expressions to English
    - Length:
        Meter: 'M'
        Kilometer: 'KM'
        Centimeter: 'CM'
        Millimeter: 'MM'
        Inch: 'INCH'
        Foot: 'FT'
        Yard: 'YD'
        Mile: 'MI'
        * Example: '80 inches' → '80 INCH', '5meter' → '5 M', 'around 500liters' → '500 L'
    - Weight:
        Kilogram: 'KG'
        Gram: 'G'
        Ton: 'T'
        Pound: 'LB'
        Ounce: 'OZ'
        * Example: '10kilos' → '10 KG', '500 grams' → '500 G', '60g' -> '60 G'
    - Storage:
        Kilobyte: 'KB'
        Megabyte: 'MB'
        Gigabyte: 'GB'
        Terabyte: 'TB'
        * Example: '256gigs' → '256 GB', '1 tera' → '1 TB'
    - Power:
        Watt: 'W'
        Kilowatt: 'KW'
        mAmpere: 'MAH'
        WattHour: 'WH'
        Volt: 'V'
        * Example: '100 watts' → '100 W', 5000 milliamphere' → '5000 MAH', 300mAh' → '300 MAH'
    - Capacity:
        Liter: 'L'
        Milliliter: 'ML'
        Gallon: 'GAL'
        Square Meter: '㎡'
        Square Centimeter: '㎠'
        Square Inch: 'INCH²'
        Sqaure Foot: 'FT²'
        * Example: '90 square meter' → '90 ㎡', '30 square cm' → '5 ㎠'
    - Channels:
        Channel: 'CH'
        * Example: '5.1 channel' → '5.1 CH'
   - This task is only applied if the expression is NOT in the exceptions list
   - Always apply standardization for Length, Weight, Storage
   - Do not apply plural forms for units, always use singular

[Exceptions for Product Spec]
- When there are multiple numbers for the same unit, keep all numbers together and do not remove the divider
    - Example: '25/22kg' → '25/22 KG'
"""
    },
    "product_price_module": {
        "KR": """
[Product Price Standardization]
- For product_price field expressions:

Task 1: Remove blank spaces and commas from numerical values
    - Convert all numbers by removing commas and spaces BETWEEN digits
    - Examples: '1 500' → '1500', '1,299' → '1299'

Task 2. Remove all spaces between numbers and currency units
    - Examples: '100만 원' → '100만원', '150 만원' → '150만원', '1 50 만원' → '150만원'

- Do not remove spaces for expressions that are not numbers or units
    - Example: '최종 혜택가' should remain as is

""",
        "GB": """
[Product Price Standardization]
- For product_price field expressions:

Task 1: Remove blank spaces and commas from numerical values
    - Convert all numbers by removing commas and spaces BETWEEN digits
    - Examples: '1 50' → '150', '1,299' → '1299'

Task 2. Remove all spaces between numbers and currency units
    - Examples: '100 pounds' → '100pounds', '150 pounds' → '150pounds', '1 50 pounds' → '150pounds'

- Do not remove spaces for expressions that are not numbers or units
    - Example: 'final price' should remain as is
"""
    },
    "product_release_date_module": {
        "KR": """
[Product Release Date Standardization]
- For product_release_date field expressions:

1. Remove spaces between the number and unit value
- Example: '2023 년 1 월 31 일' → '2023년 1월 31일', '3 분기' → '3분기'
- Warning: Do not remove spaces between different units, e.g., '2023년 1월 31일' should remain as is.

2. Remove spaces between the modifier and the unit
- Example: '지난 주' → '지난주', '지난 토요일' → '지난토요일', '1주일 전' → '1주일전', '첫 번째 금요일' → '1번째금요일'
- Warning: Keep the modifier (e.g., '지난' meaning 'last' or 'previous') directly attached to the unit (e.g., '주' meaning 'week').
- Example of 1 and 2: "2025년 첫 번 째 금요일" → "2025년 1번째금요일" as there are two different units

3. If the expression contains a number in text form, change it to a number if possible
- Example: '삼일' → '3일', '이천이십삼년' → '2023년', '칠월' → '7월', '두 번째 일요일' → '2번째일요일'
- Warning: If the expression is already in a numerical format, do not change it.

4. Standardize year expressions:
- Example: '23년', '23' → '2023년' (assume 20xx for years < 100)
- Warning: Only standardize product_release_date field expressions, not model or spec expressions

If the expression does not apply to the tasks above, do not apply any changes.

[Number and Unit Examples]
- '2024년여름' → '2024년 여름' as year and season are different units
- '2024년연말' → '2024년 연말' as year and end of the year are different units
- '2024년 9월' → '2024년 9월' as year and month are different units
""",
        "GB": """
[Product Release Date Standardization]
- For product_release_date field expressions:

1. Standardize product_release_date formats by adding MM/DD/YY identifiers where applicable:
   - For months: Add 'MM' after the month number
     - Example: 'January' → '01MM', 'Feb' → '02MM'
   - For days: Add 'DD' after the day number
     - Example: '31' → '31DD' when it's clearly a day
   - For years: Add 'YY' after the year number
     - Example: '2024' → '2024YY', '23' → '2023YY' (assume 20xx for years < 100)
   - Full date example: 'January 31, 2024' → '01MM 31DD, 2024YY'
   - Warning: Only add these identifiers when the date component is clearly identifiable from context. If the role of a number is ambiguous, follow rule 3

2. If the expression contains a number in text form, change it to a number if possible
   - Example: 'First' → '1st', 'TwentyTwentyFour' → '2024YY'
   - Warning: If the expression is already in a numerical format, do not change it.

3. Space removal rules:
   - Remove spaces between numbers and their units: '3 weeks' → '3weeks', '2 days' → '2days'
   - Remove spaces within same-unit expressions: 'less than a week' → 'lessthanaweek', 'last Tuesday' → 'lastTuesday'
   - Keep spaces between different units: '01MM 31DD 2024YY' should remain as is
   - Examples:
     Same unit (remove spaces): 'First Friday' → '1stFriday', '1 week ago' → '1weekago', 'next month' → 'nextmonth', 'every other day' → 'everyotherday', 'end of week' → 'endofweek', 'mid January' → 'mid01MM'
     Different units (keep spaces): '3weeks 2days' → '3weeks 2days', '01MM 15DD' → '01MM 15DD', '2024YY 01MM' → '2024YY 01MM', 'Q1 2024YY' → 'Q1 2024YY', '1stweek 01MM' → '1stweek 01MM'

If the expression does not apply to the tasks above, do not apply any changes.
"""
    }
}

PASS_MODULE = """
[Standardization Flag]
- This is a conditional prompt
- If this prompt is given, do not apply any changes to the expression, give the NER results as an output as given.
"""

EXAMPLE_MODULE = """
[Example]
Input (6 objects): 
[{'expression': '2024 년', 'field': 'product_release_date', 'operator': 'in'},
{'expression': '100만 원', 'field': 'product_price', 'operator': 'greater_than'},
{'expression': '1 50 만원', 'field': 'product_price', 'operator': 'less_than'},,
{'expression': '512기가', 'field': 'product_spec', 'operator': 'in'},
{'expression': '핸드폰', 'field': 'product_model', 'operator': 'in'},
{'expression': '전기세 절약', 'field': 'product_model', 'operator': 'in'}]

Output: (6 objects In the same order, applied unit standardization and spacing rules for each field)
[{'expression': '2024년', 'field': 'product_release_date', 'operator': 'in'},  // # STANDARDIZED - date
{'expression': '100만원', 'field': 'product_price', 'operator': 'greater_than'}, // # STANDARDIZED - price
{'expression': '150만원', 'field': 'product_price', 'operator': 'less_than'}, // # STANDARDIZED - price
{'expression': '512 GB', 'field': 'product_spec', 'operator': 'in'}, // # STANDARDIZED - spec
{'expression': '핸드폰', 'field': 'product_model', 'operator': 'in'}, // # UNCHANGED - not target
{'expression': '전기세 절약', 'field': 'product_option', 'operator': 'in'}] // # UNCHANGED - not target
"""