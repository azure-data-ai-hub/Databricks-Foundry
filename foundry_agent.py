import argparse
import asyncio
import os
from dataclasses import dataclass
from pathlib import Path

from agent_framework.foundry import FoundryAgent
from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv


DEFAULT_ENV_FILE = Path(__file__).with_name(".env")


def load_environment(env_file: Path = DEFAULT_ENV_FILE) -> None:
    load_dotenv(dotenv_path=env_file, override=False)


@dataclass(frozen=True)
class Settings:
    tenant_id: str
    client_id: str
    client_secret: str
    project_endpoint: str
    agent_name: str

    @classmethod
    def from_environment(cls) -> "Settings":
        required_variables = (
            "AZURE_TENANT_ID",
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET",
            "FOUNDRY_PROJECT_ENDPOINT",
            "FOUNDRY_AGENT_NAME",
        )
        missing = [name for name in required_variables if not os.getenv(name)]
        if missing:
            raise ValueError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        return cls(
            tenant_id=os.environ["AZURE_TENANT_ID"],
            client_id=os.environ["AZURE_CLIENT_ID"],
            client_secret=os.environ["AZURE_CLIENT_SECRET"],
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            agent_name=os.environ["FOUNDRY_AGENT_NAME"],
        )


async def invoke_agent(settings: Settings, user_message: str) -> str:
    credential = ClientSecretCredential(
        tenant_id=settings.tenant_id,
        client_id=settings.client_id,
        client_secret=settings.client_secret,
    )

    with (
        credential,
        AIProjectClient(
            endpoint=settings.project_endpoint,
            credential=credential,
        ) as project_client,
    ):
        agent_details = project_client.agents.get(settings.agent_name)
        agent_version = agent_details.versions.latest.version

        async with FoundryAgent(
            project_endpoint=settings.project_endpoint,
            agent_name=settings.agent_name,
            agent_version=agent_version,
            credential=credential,
        ) as agent:
            response = await agent.run(user_message)

        if not response.text:
            raise RuntimeError(
                f"Agent '{settings.agent_name}' version {agent_version} "
                "completed without a text response."
            )
        return response.text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Invoke an existing Microsoft Foundry prompt agent."
    )
    parser.add_argument(
        "message",
        nargs="?",
        default="Explain Microsoft Foundry agents in three sentences.",
        help="Message to send to the existing agent.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_environment()
    settings = Settings.from_environment()
    answer = asyncio.run(invoke_agent(settings, args.message))
    print(f"\nAgent response:\n{answer}")


if __name__ == "__main__":
    main()
