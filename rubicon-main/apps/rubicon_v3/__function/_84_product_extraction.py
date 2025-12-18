import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import time

from pydantic import BaseModel

from typing import List, Optional

from apps.rubicon_v3.__function.__llm_call import open_ai_call_structured
from apps.rubicon_v3.__function.__utils import get_prompt_from_obj
from apps.rubicon_v3.__function.definitions import response_types


class ProductExtractionItem(BaseModel):
    product_model: Optional[str]
    product_code: Optional[str]
    product_spec: Optional[str]


class ProductExtraction(BaseModel):
    product_extraction: List[ProductExtractionItem]


def product_extraction(full_response: str):
    # Grab the product extraction prompt from db
    prompt = get_prompt_from_obj(response_type=response_types.PRODUCT_EXTRACTION)

    # Prepare the messages for the LLM call
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": full_response},
    ]

    # Call the LLM to extract product information
    response = open_ai_call_structured(
        "gpt-4.1", messages, ProductExtraction, 0.01, 0.1, 42
    )

    return response


if __name__ == "__main__":
    # Example usage
    example_response = """The Series 9 and Series 6 washing machines from Samsung are designed to suit different lifestyles and laundry needs, with the Series 9 offering the most advanced features and intelligent performance, while the Series 6 focuses on smart efficiency and gentle care. Here’s a detailed comparison to help you choose the perfect fit for your home:\n\n<br><br>\n| Feature/Specification                | Series 9 Washing Machine                                                                                           | Series 6 Washing Machine                                                                                      |\n|--------------------------------------|-------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|\n| **Energy Efficiency**                | Exceeds A Grade by up to 55% (21.8kWh/100 cycles), delivering exceptional savings and eco-friendly operation.      | Exceeds A Grade by up to 10%; AI Energy mode can reduce energy use by up to 70% on selected cycles.           |\n| **AI & Smart Control**               | AI Home with intuitive touchscreen, personalised cycle suggestions, and post-wash laundry reports via SmartThings. | SmartThings AI Energy mode for monitoring and reducing energy use; remote control and cycle management.        |\n| **Detergent & Water Management**     | AI Wash senses fabric weight/soil level, adjusts water/detergent, and reduces detergent use by up to 15%.          | AI Ecobubble™ detects fabric type, adjusts bubbles/wash time/temp/spin speed for optimal cleaning and care.    |\n| **Washing Technology**               | AI Wash, Auto Dose, QuickDrive™, AddWash™, ecobubble™ for deep cleaning and time savings.                         | AI Ecobubble™ for effective cleaning in cool water, gentle on fabrics, and energy savings.                    |\n| **Capacity Options**                 | Available in 9kg (with 5-year parts & labour warranty, 20-year compressor warranty).                               | Available in 9kg and 11kg (with 20-year motor warranty on Digital Inverter Technology).                        |\n| **Fabric Care**                      | AI Wash ensures thorough cleaning with less water/detergent, tailored to each load.                               | AI Ecobubble™ provides 45.5% better fabric care, gentle washing, and up to 24% more soil removal.             |\n| **Design & User Experience**         | Premium design, advanced touchscreen controls, and personalised laundry experience.                                | Modern design, intuitive controls, and clear LCD display for straightforward operation.                        |\n\n---\n\n### How Each Series Fits Your Lifestyle\n\n- **Series 9**:  \n  - Perfect for those who want the ultimate in smart home integration, energy savings, and laundry personalisation.\n  - The AI Home system learns your habits, suggests cycles, and provides detailed laundry reports, making every wash effortless and tailored.\n  - Advanced technologies like QuickDrive™ and AddWash™ save time and let you add forgotten items mid-cycle, ideal for busy families or tech enthusiasts.\n\n- **Series 6**:  \n  - Designed for households seeking reliable, energy-efficient washing with gentle fabric care.\n  - AI Ecobubble™ ensures deep cleaning even at lower temperatures, protecting your clothes and saving on bills.\n  - The SmartThings AI Energy mode helps you monitor and reduce energy use, making it a smart choice for eco-conscious users.\n\n### Key Technologies Explained\n\n- **AI Wash (Series 9)**:  \n  - Automatically senses load size and soil level, adjusting water, detergent, and cycle time for optimal results.\n  - Reduces detergent use by analysing previous cycles, ensuring efficiency and fabric protection.\n\n- **AI Ecobubble™ (Series 6)**:  \n  - Creates bubbles that penetrate fabrics quickly, removing more soil even in cool water.\n  - Adjusts washing parameters based on fabric type for gentle, effective cleaning.\n\n- **SmartThings Integration**:  \n  - Both Series 9 and Series 6 connect to the SmartThings app, allowing remote control, energy monitoring, and cycle management from your smartphone.\n\n---\n\n**In summary:**  \nIf you want the most advanced, personalised, and energy-saving laundry experience, the Series 9 is the top choice. For smart, efficient, and gentle washing with excellent value, the Series 6 is a fantastic option. Both deliver outstanding performance, but Series 9 takes smart laundry to the next level. If you’d like to know more about specific models or need help choosing the right capacity, just let me know!"""

    response = product_extraction(example_response)

    print(response)
