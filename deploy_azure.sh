#!/usr/bin/env bash
# Automated Azure Cloud Production Deployment script for ForgeOne AI

set -e

RESOURCE_GROUP="rg-forgeone-ai-prod"
LOCATION="eastus"
OPENAI_NAME="forgeone-openai-prod"
SEARCH_NAME="forgeone-search-prod"
ACR_NAME="acrforgeoneai"
CONTAINER_APP_NAME="forgeone-backend"

echo "====================================================="
echo "  ForgeOne AI — Azure Automated Production Deployment"
echo "====================================================="

echo "[1/5] Creating Resource Group '$RESOURCE_GROUP' in $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" > /dev/null
echo "✓ Resource group created."

echo "[2/5] Deploying Azure OpenAI Service ($OPENAI_NAME)..."
az cognitiveservices account create \
  --name "$OPENAI_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --kind OpenAI \
  --sku S0 > /dev/null

echo "Deploying gpt-4o chat model..."
az cognitiveservices account deployment create \
  --name "$OPENAI_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --deployment-name "gpt-4o" \
  --model-name "gpt-4o" \
  --model-version "2024-08-06" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard > /dev/null

echo "Deploying text-embedding-3-large embedding model..."
az cognitiveservices account deployment create \
  --name "$OPENAI_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --deployment-name "text-embedding-3-large" \
  --model-name "text-embedding-3-large" \
  --model-version "1" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard > /dev/null
echo "✓ Azure OpenAI models deployed."

echo "[3/5] Deploying Azure AI Search ($SEARCH_NAME)..."
az search service create \
  --name "$SEARCH_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Basic > /dev/null
echo "✓ Azure AI Search deployed."

echo "[4/5] Provisioning Azure Container Registry ($ACR_NAME)..."
az acr create \
  --name "$ACR_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --sku Basic \
  --admin-enabled true > /dev/null

echo "Building Docker image in ACR..."
az acr build \
  --registry "$ACR_NAME" \
  --image "forgeone-backend:latest" \
  backend/
echo "✓ Backend container image built."

echo "[5/5] Deploying Azure Container Apps..."
ENV_NAME="cae-forgeone-ai"
az containerapp env create \
  --name "$ENV_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" > /dev/null

OPENAI_ENDPOINT=$(az cognitiveservices account show --name "$OPENAI_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.endpoint" -o tsv)
SEARCH_ENDPOINT="https://${SEARCH_NAME}.search.windows.net"

az containerapp create \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENV_NAME" \
  --image "${ACR_NAME}.azurecr.io/forgeone-backend:latest" \
  --target-port 8000 \
  --ingress external \
  --system-assigned \
  --env-vars \
    "ENVIRONMENT=production" \
    "AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT" \
    "AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT" \
    "AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-large" \
    "AZURE_CHAT_DEPLOYMENT=gpt-4o" \
    "AZURE_SEARCH_INDEX_NAME=supplier-facts" > /dev/null

BACKEND_FQDN=$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)
echo "====================================================="
echo " 🎉 Azure Deployment Successful!"
echo " Backend API FQDN: https://${BACKEND_FQDN}"
echo " Swagger API Docs: https://${BACKEND_FQDN}/docs"
echo "====================================================="
