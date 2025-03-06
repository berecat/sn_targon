import asyncio
from targon.config import (
    AUTO_UPDATE,
    HEARTBEAT,
    IS_TESTNET,
    SLIDING_WINDOW,
    get_models_from_config,
    get_models_from_endpoint,
    load_public_key,
)
from targon.docker import load_docker, load_existing_images, sync_output_checkers
from targon.types import Config
from targon.config import add_miner_args, load_config_file
import random
import bittensor as bt
from bittensor import logging
logging.set_debug()
from targon.dataset import download_dataset, download_tool_dataset
from targon.request import check_tokens, generate_request
from targon.types import Endpoints, InferenceStats
import time
from typing import Dict, Any
import openai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAPI_KEY")
    
async def send_request(request: Dict[str, Any], endpoint: Endpoints, stats: Any):
    """
    Sends a request to OpenAI's API and processes streaming responses.

    :param request: The request payload for OpenAI API.
    :param endpoint: Either 'chat' (ChatCompletion) or 'completion' (TextCompletion).
    :param stats: Object to store response tokens for tracking.
    """
    start_token_time = 0
    start_send_message_time = time.time()
    token_times = []
    origin_model = request["model"]

    try:
        match endpoint:
            case Endpoints.CHAT:
                request["model"] = "gpt-4o"
                request["logprobs"] = True
                client = openai.AsyncOpenAI(
                    api_key=api_key,  # Replace with your actual API key
                    max_retries=0,
                    timeout=openai.Timeout(60, connect=5, read=5),
                )
                chat = await client.chat.completions.create(**request)
                async for chunk in chat:
                    # Store raw chunk
                    stats.tokens.append(chunk.model_dump())

                    # Track timing
                    if start_token_time == 0:
                        start_token_time = time.time()
                    token_times.append(time.time())

            case Endpoints.COMPLETION:
                request["logprobs"] = 5
                request["model"] = "gpt-4o-mini"
                client = openai.AsyncOpenAI(
                    api_key=api_key,  # Replace with your actual API key
                    max_retries=0,
                    timeout=openai.Timeout(60, connect=5, read=5),
                )
                comp = await client.completions.create(**request)
                async for chunk in comp:
                    # Store raw chunk
                    stats.tokens.append(chunk.model_dump())

                    # Track timing
                    if start_token_time == 0:
                        start_token_time = time.time()
                    token_times.append(time.time())
                    
        print('response generated')
        
    except openai.APIConnectionError as e:
        bt.logging.trace(f"failed request: {e}")
        stats.error = str(e)
        stats.cause = "BAD_STREAM"
    except Exception as e:
        bt.logging.error(f"Unknown Error when sending to miner {e}")
        stats.error = str(e)
        stats.cause = "BAD_STREAM"
        
    if stats.error:
        return stats

    if start_token_time == 0:
        start_token_time = time.time()
    end_token_time = time.time()

    stats.time_to_first_token = start_token_time - start_send_message_time
    stats.time_for_all_tokens = end_token_time - start_token_time
    stats.total_time = end_token_time - start_send_message_time
    stats.tps = min(len(stats.tokens), request["max_tokens"]) / stats.total_time

    request["model"] = origin_model
    return stats

async def handle_inference(
    request,
    endpoint
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
    
    return await send_request(
        request,
        endpoint,
        stats
    )
    
    

class RequestMock:
    config_file: Config
    def __init__(self):
        self.client = load_docker()
        self.config_file = load_config_file()
        bt.logging.info("⌛️", "Loading datasets")
        self.dataset = download_dataset()
        self.tool_dataset = download_tool_dataset()

    def get_models(self):
        models = get_models_from_config()
        return models
    
    async def verify_response(self, request, endpoint, stat: InferenceStats):
        if stat.error or stat.cause:
            return stat
        # We do this out of the handle_inference loop to not block other requests
        verification_port = self.verification_ports.get(request["model"], {}).get(
            "port"
        )
        verification_url = self.verification_ports.get(request["model"], {}).get("url")
        if verification_port is None or verification_url is None:
            bt.logging.error(
                "Send request to a miner without verification port for model"
            )
            return None
        verified, err = await check_tokens(
            request,
            stat.tokens,
            endpoint=endpoint,
            port=verification_port,
            url=verification_url,
        )
        if err is not None or verified is None:
            print(f"{err}")
            bt.logging.error(
                f"Failed checking tokens for on model {request['model']}: {err}"
            )
            return None
        stat.verified = (
            verified.get("verified", False) if verified is not None else False
        )
        if stat.verified:
            print("verified!")
            tokencount = min(len(stat.tokens), request["max_tokens"])
            response_tokens = int(verified.get("response_tokens", 0))
            if response_tokens:
                tokencount = min(tokencount, response_tokens)
            stat.tps = tokencount / stat.total_time
            stat.gpus = verified.get("gpus", 1)
        if stat.error is None and not stat.verified:
            stat.error = verified.get("error")
            stat.cause = verified.get("cause")    
            print(f"{stat.error}")

    async def query_miners(self, model_name, endpoint, generator_model_name, should_score: bool,):
        while True:
            request = generate_request(
                self.dataset,
                self.tool_dataset,
                model_name,
                endpoint,
                self.verification_ports.get(generator_model_name),
            )
            
            bt.logging.info("Generated Request")
            
            stat = await handle_inference(request, endpoint)
            response = await self.verify_response(
                request, endpoint, stat
            )
            
            time.sleep(10)
        
        
        
        print("done")

    async def run(self):
        try:
            models = self.get_models()
            extra = []
            self.models = list(set([m["model"] for m in models] + extra))
            
            self.verification_ports = sync_output_checkers(
                self.client, models, self.config_file, extra
            )
            
            model_name = random.choice(self.models)
            
            models = [m["model"] for m in models]
            generator_model_name = random.choice(
                list(
                    (set(models) - set(extra))
                    & set(self.verification_ports.keys())
                )
            )

            
            if self.verification_ports.get(model_name) != None:
                endpoint = random.choice(
                    self.verification_ports[model_name]["endpoints"]
                )
            else:
                endpoint = random.choice(
                    self.verification_ports[generator_model_name]["endpoints"]
                )
                
            endpoint = Endpoints.CHAT
                
            bt.logging.info("Mocking query_miners ---------")
            
            res = await self.query_miners(
                model_name,
                endpoint,
                generator_model_name,
                model_name in list(self.verification_ports.keys()),
            )
            
        except Exception as e:
            print(f"{e}")

if __name__ == "__main__":
    request_mock = RequestMock()
    asyncio.run(request_mock.run())
