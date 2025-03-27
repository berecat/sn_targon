import httpx
import asyncio
import json
from typing import Dict, Any
from targon.types import Endpoints, InferenceStats
import time
import bittensor as bt
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse

async def send_request(
    request: Dict[str, Any], endpoint: Endpoints, stats: Any
):
    stats = InferenceStats(
        gpus=1,
        time_to_first_token=0,
        time_for_all_tokens=0,
        tps=0,
        total_time=0,
        tokens=[],
        verified=False,
    )
    
    # start_token_time = 0
    start_send_message_time = time.time()
    token_times = []
    
    try:
        match endpoint:
            case Endpoints.CHAT:
                async def stream_chat(request_data):
                    async with httpx.AsyncClient(timeout=httpx.Timeout(180)) as client:
                        req = client.build_request(
                            "POST",
                            "http://localhost:8000/v1/chat/completions",
                            json=request_data,
                        )
                        response = await client.send(req, stream=True)
                        async for line in response.aiter_lines():
                            if line.startswith("data:"):
                                raw_data = line[len("data:"):].strip()
                                if raw_data == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(raw_data)
                                    stats.tokens.append(chunk)

                                    now = time.time()
                                    # if start_token_time == 0:
                                    #     start_token_time = now
                                    token_times.append(now)

                                    # Optional: print or log streaming output
                                    content = chunk["choices"][0]["delta"].get("content", "")
                                    print(content, end="", flush=True)

                                except json.JSONDecodeError as e:
                                    print("Failed to decode chunk:", line)

                    end_time = time.time()
                    # stats.time_to_first_token = start_token_time - start_send_message_time
                    # stats.time_for_all_tokens = end_time - start_token_time
                    # stats.total_time = end_time - start_send_message_time
                    # stats.tps = len(token_times) / stats.time_for_all_tokens if stats.time_for_all_tokens > 0 else 0

                    return stats
                
                stats = await stream_chat(request)
                print('d')
                # async for chunk in r.aiter_raw():
                #     chunk = chunk.decode("utf-8")
                    
                #     if chunk.startswith("data: "):
                #         chunk = chunk[len("data: "):].strip()
                        
                #         if chunk != "[DONE]":
                #             stats.tokens.append(json.loads(chunk))
                    # print(f"{chunk}")
                # return StreamingResponse(
                #     r.aiter_raw(), background=BackgroundTask(r.aclose), headers=r.headers
                # )
                # async for chunk in r.aiter_raw():
                #     # Store raw chunk
                #     chunk = chunk.decode("utf-8")
                #     if chunk.startswith("data: "):  # Remove prefix
                #         chunk = chunk[len("data: "):].strip()
                #     dict_chunk = json.loads(chunk)
                #     stats.tokens.append(dict_chunk)

                #     # Track timing
                #     if start_token_time == 0:
                #         start_token_time = time.time()
                #     token_times.append(time.time())

            # case Endpoints.COMPLETION:
            #     request["logprobs"] = 5
            #     request["model"] = "gpt-4o-mini"
            #     client = openai.AsyncOpenAI(
            #         api_key=api_key,  # Replace with your actual API key
            #         max_retries=0,
            #         timeout=openai.Timeout(60, connect=5, read=5),
            #     )
            #     comp = await client.completions.create(**request)
            #     async for chunk in comp:
            #         # Store raw chunk
            #         stats.tokens.append(chunk.model_dump())

            #         # Track timing
            #         if start_token_time == 0:
            #             start_token_time = time.time()
            #         token_times.append(time.time())
                    
        print('response generated')
        
    # except openai.APIConnectionError as e:
    #     bt.logging.trace(f"failed request: {e}")
    #     stats.error = str(e)
    #     stats.cause = "BAD_STREAM"
    except Exception as e:
        bt.logging.error(f"Unknown Error when sending to miner {e}")
        stats.error = str(e)
        stats.cause = "BAD_STREAM"
        
    if stats.error:
        return stats

    # if start_token_time == 0:
    #     start_token_time = time.time()
    # end_token_time = time.time()

    # stats.time_to_first_token = start_token_time - start_send_message_time
    # stats.time_for_all_tokens = end_token_time - start_token_time
    # stats.total_time = end_token_time - start_send_message_time
    # stats.tps = min(len(stats.tokens), request["max_tokens"]) / stats.total_time

    return stats

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