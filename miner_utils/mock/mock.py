import httpx
import asyncio
import json

async def run():
    try:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(60 * 3),
            base_url="http://localhost:8000/v1",
            # headers={"Authorization": f"Bearer {self.config_file.miner_api_key}"},
        )
        
        request = {'seed': 2792987, 'max_tokens': 1046, 'temperature': 0.6075127626626474, 'model': 'EnvyIrys/EnvyIrys_sn111_14', 'stream': True, 'stream_options': {'include_usage': True}, 'logprobs': True, 'messages': [{'role': 'system', 'content': '"\\n### Current Date: 2025-03-06\\n### Instruction:\\nYou are to take on the role of Belvia, an expert language model\\ndeveloped in Greece, tasked with generating responses to user queries.\\nYour answer should be relevant to the query, and you must start all responses\\nby briefly introducing yourself, re-stating the query in your own words from \\nyour perspective ensuring you include today\'s date (which was provided above),\\nthen provide the response to the query. You should always respond in English.\\n"'}, {'role': 'user', 'content': '["system: \\n### Current Date: 2025-03-06\\n### Instruction:\\nYou are to take the query information that is passed from you and create a search query for the query data. \\nDo not answer the information, just create a search query. The search query should be short and no and longer than a sentence.\\nAssistant should always start the response with \\"Search query: \\"\\n\\nuser: Tool available:\\n[1] Python interpreter\\nWhen you send a message containing Python code to python, it will be executed in a stateful Jupyter notebook environment.\\nSolve the following math problem step-by-step.\\ntoday joelle opened an interest - bearing savings account and deposited $ 5,000 . if the annual interest rate is 4 percent compounded interest , and she neither deposits nor withdraws money for exactly 2 years , how much money will she have in the account ?\\n\\nResponse:  Search query: \\n\\"today joelle opened an interest - bearing savings account and deposited $ 5,000. if the annual interest rate is 4 percent compounded interest, and she neither deposits nor withdraws money"]'}]
    }



        
        req = client.build_request(
            "POST", "/chat/completions", json=request
        )
        
        r = await client.send(req, stream=True)
        
        async for chunk in r.aiter_raw():
            print(f"{chunk}")
        
        print("h")
    except Exception as e:
        print(f"{e}")
    
if __name__ == "__main__":
    asyncio.run(run())