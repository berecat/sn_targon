import os
import json
import asyncio
import random
from datetime import datetime
from openai import OpenAI
from typing import Dict, Union, Iterable
from os import urandom
import time

async def run():
    random.seed(urandom(100))
    seed = random.randint(10000, 10000000)
    temperature = random.random()
    max_tokens = random.randint(512, 2048)

    try:
        start_send_message_time = time.time()
        client = OpenAI(
            api_key="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"
        )

        # # Generate prompt dynamically
        # search_query = "A car travels a distance of 200 km in 2 hours. Use the Mean Value Theorem to find a time during the 2 hours where the car's instantaneous speed is equal to its average speed."
        # search_prompt = create_search_prompt(search_query, Endpoints.COMPLETION)

        # API call with corrected prompt
        chat = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "\"\\n### Current Date: 2025-03-06\\n### Instruction:\\nYou are to take on the role of Karry, an expert language model\\ndeveloped in Cabo Verde, tasked with generating responses to user queries.\\nYour answer should be relevant to the query, and you must start all responses\\nby briefly introducing yourself, re-stating the query in your own words from \\nyour perspective ensuring you include today's date (which was provided above),\\nthen provide the response to the query. You should always respond in English.\\n\""
                },
                {
                    "role": "user",
                    "content": "[\"system: \\n### Current Date: 2025-03-06\\n### Instruction:\\nYou are to take the query information that is passed from you and create a search query for the query data. \\nDo not answer the information, just create a search query. The search query should be short and no and longer than a sentence.\\nAssistant should always start the response with \\\"Search query: \\\"\\n\\nuser: Do these questions have the same meaning?\\nCan server based Android games be hacked?\\nWhat's the Android game you want to be hacked most?\\n\\nAvailable choices: -- no. -- yes.\\n\\nResponse:  Search query: \\\"Do these questions have the same meaning?\\\" - no. - \\\"Can server based Android games be hacked?\\\" - yes. - \\\"What's the Android game you want to be hacked most?\\\" - \\\"Minecraft\\\".\"]"
                }
            ]
        )
            # print(chunk.choices[0].text)
        tokens = []
        
        for chunk in chat:
            tokens.append(chunk)
            
        end_time = time.time()
        
        print('done')

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
