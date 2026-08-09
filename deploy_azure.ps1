<#
.SYNOPSIS
Automated Azure Cloud Production Deployment script for ForgeOne AI.

.DESCRIPTION
Provisions Azure Resource Group, Azure OpenAI (gpt-4o & text-embedding-3-large),
Azure AI Search, Azure Container Registry, Azure Container Apps, and Azure Static Web Apps.
#>

param (
    [string]$ResourceGroup = "rg-forgeone-ai-prod",
    [string]$Location = "eastus",
    [string]$SearchLocation = "eastus",
    [string]$OpenAIName = "forgeone-openai-prod",
    [string]$SearchName = "forgeone-search-prod",
    [string]$AcrName = "acrforgeoneai",
    [string]$ContainerAppName = "forgeone-backend",
    [string]$StaticWebAppName = "forgeone-frontend"
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  ForgeOne AI — Azure Automated Production Deployment" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Resource Group
Write-Host "`n[1/6] Creating Resource Group '$ResourceGroup' in $Location..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location | Out-Null
Write-Host "✓ Resource group created." -ForegroundColor Green

# 2. Azure OpenAI / Foundry
Write-Host "`n[2/6] Deploying Azure OpenAI Service ($OpenAIName)..." -ForegroundColor Yellow
az cognitiveservices account create `
  --name $OpenAIName `
  --resource-group $ResourceGroup `
  --location $Location `
  --kind OpenAI `
  --sku S0 | Out-Null

Write-Host "Deploying gpt-4o chat model..." -ForegroundColor Yellow
az cognitiveservices account deployment create `
  --name $OpenAIName `
  --resource-group $ResourceGroup `
  --deployment-name "gpt-4o" `
  --model-name "gpt-4o" `
  --model-version "2024-08-06" `
  --model-format OpenAI `
  --sku-capacity 10 `
  --sku-name Standard | Out-Null

Write-Host "Deploying text-embedding-3-large embedding model..." -ForegroundColor Yellow
az cognitiveservices account deployment create `
  --name $OpenAIName `
  --resource-group $ResourceGroup `
  --deployment-name "text-embedding-3-large" `
  --model-name "text-embedding-3-large" `
  --model-version "1" `
  --model-format OpenAI `
  --sku-capacity 10 `
  --sku-name Standard | Out-Null
Write-Host "✓ Azure OpenAI models deployed." -ForegroundColor Green

# 3. Azure AI Search
Write-Host "`n[3/6] Deploying Azure AI Search ($SearchName)..." -ForegroundColor Yellow
az search service create `
  --name $SearchName `
  --resource-group $ResourceGroup `
  --location $SearchLocation `
  --sku Basic | Out-Null
Write-Host "✓ Azure AI Search deployed." -ForegroundColor Green

# 4. Azure Container Registry & Build
Write-Host "`n[4/6] Provisioning Azure Container Registry ($AcrName)..." -ForegroundColor Yellow
az acr create `
  --name $AcrName `
  --resource-group $ResourceGroup `
  --sku Basic `
  --admin-enabled true | Out-Null

Write-Host "Building Docker image in Azure Container Registry..." -ForegroundColor Yellow
az acr build `
  --registry $AcrName `
  --image "forgeone-backend:latest" `
  backend/
Write-Host "✓ Backend container image built." -ForegroundColor Green

# 5. Azure Container Apps
Write-Host "`n[5/6] Deploying Azure Container Apps Environment & Backend App..." -ForegroundColor Yellow
$EnvName = "cae-forgeone-ai"
az containerapp env create `
  --name $EnvName `
  --resource-group $ResourceGroup `
  --location $Location | Out-Null

$OpenAiEndpoint = az cognitiveservices account show --name $OpenAIName --resource-group $ResourceGroup --query "properties.endpoint" -o tsv
$SearchEndpoint = "https://$SearchName.search.windows.net"

az containerapp create `
  --name $ContainerAppName `
  --resource-group $ResourceGroup `
  --environment $EnvName `
  --image "$AcrName.azurecr.io/forgeone-backend:latest" `
  --target-port 8000 `
  --ingress external `
  --system-assigned `
  --env-vars `
    "ENVIRONMENT=production" `
    "AZURE_OPENAI_ENDPOINT=$OpenAiEndpoint" `
    "AZURE_SEARCH_ENDPOINT=$SearchEndpoint" `
    "AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-large" `
    "AZURE_CHAT_DEPLOYMENT=gpt-4o" `
    "AZURE_SEARCH_INDEX_NAME=supplier-facts" | Out-Null

Write-Host "✓ Backend Container App deployed." -ForegroundColor Green

# 6. Summary Output
$BackendFqdn = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host " 🎉 Azure Deployment Successful!" -ForegroundColor Green
Write-Host " Backend API FQDN: https://$BackendFqdn" -ForegroundColor White
Write-Host " Swagger API Docs: https://$BackendFqdn/docs" -ForegroundColor White
Write-Host "=====================================================" -ForegroundColor Cyan
