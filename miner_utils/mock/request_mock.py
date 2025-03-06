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

class RequestMock:
    config_file: Config
    def __init__(self):
        self.client = load_docker()
        self.config_file = load_config_file()

    def get_models(self):
        models = get_models_from_config()
        return models

    async def run(self):
        models = self.get_models()
        extra = []
        
        self.verification_ports = sync_output_checkers(
            self.client, models, self.config_file, extra
        )
        
        model_name = random.choice(self.models)
        generator_model_name = random.choice(
                list(
                    (set(models) - set(extra))
                    & set(list(self.verification_ports.keys()))
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


if __name__ == "__main__":
    request_mock = RequestMock()
    asyncio.run(request_mock.run())
