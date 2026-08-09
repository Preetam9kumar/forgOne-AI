# Azure Cloud Production Deployment Guide — ForgeOne AI

This guide details the complete production deployment process for **ForgeOne AI** on **Microsoft Azure Cloud**, utilizing **Azure AI Foundry / Azure OpenAI** (`gpt-4o` and `text-embedding-3-large`), **Azure AI Search**, **Azure Container Apps** (backend), and **Azure Static Web Apps** (frontend).

---

## 🏛️ Azure Production Architecture

```
                    ┌─────────────────────────┐
                    │  Azure Static Web Apps  │
                    │  (React Vite Frontend)  │
                    └────────────┬────────────┘
                                 │ HTTPS API Calls
                                 ▼
                    ┌─────────────────────────┐
                    │  Azure Container Apps   │
                    │  (FastAPI Python API)   │
                    └────────────┬────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │ Managed Identity    │ Managed Identity    │ Managed Identity
           ▼                     ▼                     ▼
┌──────────────────────┐ ┌───────────────────┐ ┌──────────────────────────┐
│ Azure AI Foundry /   │ │  Azure AI Search  │ │ Azure DB for PostgreSQL  │
│ Azure OpenAI Service │ │  (Vector Index)   │ │ Flexible Server (SQL DB) │
│ • gpt-4o             │ │ • supplier-facts  │ └──────────────────────────┘
│ • text-embedding-    │ └───────────────────┘
│   3-large (3072 dims)│
└──────────────────────┘
```

---

## 📋 Prerequisites & Tools

1. **Azure CLI** installed (`az --version`).
2. Active **Azure Subscription** with permissions to create Resource Groups, AI Services, Container Apps, and Static Web Apps.
3. **Docker Desktop** or container build tools (`az acr build`).
4. Python 3.10+ and Node.js 18+.

---

## 🚀 Quick Automated Deployment (One-Command)

Run either script from the project root directory:

### Windows (PowerShell):
```powershell
.\deploy_azure.ps1 -ResourceGroup "rg-forgeone-ai-prod" -Location "eastus"
```

### Linux / macOS (Bash):
```bash
chmod +x ./deploy_azure.sh
./deploy_azure.sh -g rg-forgeone-ai-prod -l eastus
```

---

## 🛠️ Step-by-Step Manual Deployment Guide

### Step 1: Login & Set Active Subscription
```bash
az login
az account set --subscription "<Your-Subscription-ID>"
```

### Step 2: Create Resource Group
```bash
az group create --name rg-forgeone-ai-prod --location eastus
```

### Step 3: Deploy Azure OpenAI / Foundry Models
Deploy **`gpt-4o`** for explanations and **`text-embedding-3-large`** (3072 dimensions) for vector search:

```bash
# Create Cognitive Services / OpenAI resource
az cognitiveservices account create \
  --name forgeone-ai-openai \
  --resource-group rg-forgeone-ai-prod \
  --location eastus \
  --kind OpenAI \
  --sku S0

# Deploy gpt-4o chat model
az cognitiveservices account deployment create \
  --name forgeone-ai-openai \
  --resource-group rg-forgeone-ai-prod \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-08-06" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard

# Deploy text-embedding-3-large embedding model
az cognitiveservices account deployment create \
  --name forgeone-ai-openai \
  --resource-group rg-forgeone-ai-prod \
  --deployment-name text-embedding-3-large \
  --model-name text-embedding-3-large \
  --model-version "1" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard
```

### Step 4: Create Azure AI Search Service
```bash
az search service create \
  --name forgeone-ai-search \
  --resource-group rg-forgeone-ai-prod \
  --location eastus \
  --sku Basic
```

### Step 5: Provision Azure Container Registry (ACR) & Build Container
```bash
# Create ACR
az acr create \
  --name acrforgeoneai \
  --resource-group rg-forgeone-ai-prod \
  --sku Basic \
  --admin-enabled true

# Build & Push container image directly in Azure
az acr build \
  --registry acrforgeoneai \
  --image forgeone-backend:v1 \
  backend/
```

### Step 6: Deploy Backend on Azure Container Apps (ACA)
```bash
# Create Container Apps Environment
az containerapp env create \
  --name cae-forgeone-ai \
  --resource-group rg-forgeone-ai-prod \
  --location eastus

# Deploy Container App
az containerapp create \
  --name forgeone-backend \
  --resource-group rg-forgeone-ai-prod \
  --environment cae-forgeone-ai \
  --image acrforgeoneai.azurecr.io/forgeone-backend:v1 \
  --target-port 8000 \
  --ingress external \
  --system-assigned \
  --env-vars \
    ENVIRONMENT=production \
    AZURE_OPENAI_ENDPOINT=https://forgeone-ai-openai.openai.azure.com/ \
    AZURE_SEARCH_ENDPOINT=https://forgeone-ai-search.search.windows.net \
    AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-large \
    AZURE_CHAT_DEPLOYMENT=gpt-4o \
    AZURE_SEARCH_INDEX_NAME=supplier-facts
```

### Step 7: Assign Managed Identity RBAC Roles
Grant the Container App permission to access Azure OpenAI and Azure Search securely without API keys:

```bash
# Get Principal ID of Container App Managed Identity
PRINCIPAL_ID=$(az containerapp show --name forgeone-backend --resource-group rg-forgeone-ai-prod --query identity.principalId -o tsv)

# Cognitive Services OpenAI User role assignment
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/<Your-Subscription-ID>/resourceGroups/rg-forgeone-ai-prod/providers/Microsoft.CognitiveServices/accounts/forgeone-ai-openai"

# Search Index Data Contributor role assignment
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Search Index Data Contributor" \
  --scope "/subscriptions/<Your-Subscription-ID>/resourceGroups/rg-forgeone-ai-prod/providers/Microsoft.Search/searchServices/forgeone-ai-search"
```

### Step 8: Deploy Frontend on Azure Static Web Apps
```bash
# Create Azure Static Web App
az staticwebapp create \
  --name forgeone-frontend \
  --resource-group rg-forgeone-ai-prod \
  --location eastus2
```

Configure backend URL on the Static Web App environment settings:
```bash
BACKEND_URL=$(az containerapp show --name forgeone-backend --resource-group rg-forgeone-ai-prod --query properties.configuration.ingress.fqdn -o tsv)

# Set CORS on backend container app
az containerapp ingress cors update \
  --name forgeone-backend \
  --resource-group rg-forgeone-ai-prod \
  --allowed-origins "https://$(az staticwebapp show --name forgeone-frontend --query defaultHostname -o tsv)"
```

---

## 🔒 Security & Best Practices Summary

1. **Keyless Authentication**: Uses Azure `DefaultAzureCredential` and Managed Identities for secure RBAC access to OpenAI and AI Search.
2. **CORS Isolation**: Restricts backend ingress CORS strictly to the domain of the Azure Static Web App.
3. **Database Migration**: Run `alembic upgrade head` upon configuring PostgreSQL connection strings in `DATABASE_URL`.
4. **Environment Isolation**: Separate `.env.example` configurations provided for local SQLite vs production Azure PostgreSQL.
