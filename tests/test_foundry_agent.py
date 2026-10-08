import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from foundry_agent import Settings, load_environment


class SettingsTests(unittest.TestCase):
    def test_loads_settings_from_dotenv_without_overriding_process_environment(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary_directory:
            env_file = Path(temporary_directory) / ".env"
            env_file.write_text(
                "\n".join(
                    (
                        "AZURE_TENANT_ID=dotenv-tenant",
                        "AZURE_CLIENT_ID=dotenv-client",
                        "AZURE_CLIENT_SECRET=dotenv-secret",
                        "FOUNDRY_PROJECT_ENDPOINT=https://example.test/api/projects/project",
                        "FOUNDRY_AGENT_NAME=dotenv-agent",
                    )
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ, {"FOUNDRY_AGENT_NAME": "process-agent"}, clear=True
            ):
                load_environment(env_file)
                settings = Settings.from_environment()

        self.assertEqual(settings.tenant_id, "dotenv-tenant")
        self.assertEqual(settings.agent_name, "process-agent")

    def test_reads_required_settings(self) -> None:
        environment = {
            "AZURE_TENANT_ID": "tenant",
            "AZURE_CLIENT_ID": "client",
            "AZURE_CLIENT_SECRET": "secret",
            "FOUNDRY_PROJECT_ENDPOINT": "https://example.test/api/projects/project",
            "FOUNDRY_AGENT_NAME": "existing-agent",
        }

        with patch.dict(os.environ, environment, clear=True):
            settings = Settings.from_environment()

        self.assertEqual(settings.tenant_id, "tenant")
        self.assertEqual(settings.agent_name, "existing-agent")

    def test_reports_all_missing_required_settings(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                ValueError,
                "AZURE_TENANT_ID.*AZURE_CLIENT_ID.*AZURE_CLIENT_SECRET"
                ".*FOUNDRY_PROJECT_ENDPOINT.*FOUNDRY_AGENT_NAME",
            ):
                Settings.from_environment()
if __name__ == "__main__":
    unittest.main()
