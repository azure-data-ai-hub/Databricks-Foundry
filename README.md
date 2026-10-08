# Microsoft Foundry agent with a service principal

This Python sample invokes an existing Microsoft Foundry prompt agent through
the Responses API. Authentication uses
`ClientSecretCredential`, so no interactive user sign-in is required.

## Prerequisites

- Python 3.10 or newer
- An existing Microsoft Foundry project and prompt agent
- A Microsoft Entra service principal with the **Foundry User** role assigned
  at the Foundry project scope

Use the service principal's object ID when creating the role assignment:

```powershell
az role assignment create `
  --assignee-object-id "<service-principal-object-id>" `
  --assignee-principal-type ServicePrincipal `
  --role "Foundry User" `
  --scope "<foundry-project-resource-id>"
```

The client ID used by the application and the service principal object ID used
for RBAC are different values.

## Set up

Create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file at the project root using `.env.example` as the template:

```dotenv
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<application-client-id>
AZURE_CLIENT_SECRET=<client-secret>
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_AGENT_NAME=<existing-agent-name>
```

The script loads this file automatically. Values already set in the process
environment take precedence over values in `.env`. Do not commit `.env` or the
client secret.

For production, load the secret from a secure secret store such as Azure Key
Vault instead of placing it in source code or a checked-in environment file.
When the caller runs in Azure, prefer a managed identity over a client secret.

## Invoke the existing agent

```powershell
python .\foundry_agent.py "What can you help me with?"
```

The `.env.example` file documents the required variable names and is safe to
commit because it contains placeholders only.

## MCP tool consent

The service principal authenticates the application to the Foundry project.
An agent tool can require separate authorization. If the response contains an
OAuth consent request, the script prints the tool name and consent URL instead
of displaying an empty response. Complete that consent and run the command
again.

For unattended service-principal execution, configure the MCP connection with
application authentication supported by that server instead of delegated user
OAuth.

## References

- [Microsoft Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/overview)
- [Azure Identity client secret credential](https://learn.microsoft.com/python/api/azure-identity/azure.identity.clientsecretcredential)
- [Foundry role-based access control](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry)
