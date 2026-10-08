import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv
from openai.types.responses import Response


DEFAULT_ENV_FILE = Path(__file__).with_name(".env")


def load_environment(env_file: Path = DEFAULT_ENV_FILE) -> None:
    load_dotenv(dotenv_path=env_file, override=False)


def extract_response_text(response: Response) -> str:
    if response.output_text:
        return response.output_text

    for item in response.output:
        if item.type == "oauth_consent_request":
            raise RuntimeError(
                f"Agent tool '{item.server_label}' requires OAuth consent. "
                f"Open this URL, complete consent, and run the command again:\n"
                f"{item.consent_link}"
            )

    output_types = ", ".join(item.type for item in response.output) or "none"
    raise RuntimeError(
        "The agent completed without a text response. "
        f"Response status: {response.status}; output types: {output_types}."
    )


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


def invoke_agent(settings: Settings, user_message: str) -> str:
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
        project_client.get_openai_client() as openai_client,
    ):
        response = openai_client.responses.create(
            input=user_message,
            extra_body={
                "agent_reference": {
                    "name": settings.agent_name,
                    "type": "agent_reference",
                }
            },
        )
        return extract_response_text(response)


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
    answer = invoke_agent(settings, args.message)
    print(f"\nAgent response:\n{answer}")


if __name__ == "__main__":
    main()
