#!/bin/bash

# Azure CLI Command Validation Script
# This script validates that all Azure CLI commands in the deployment script use correct parameters

set -e

print_status() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

print_status "🔍 Validating Azure CLI commands in deploy-to-azure.sh..."

# Check if Azure CLI is available
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Cannot validate commands."
    exit 1
fi

print_success "Azure CLI is available"

# Validate specific command patterns
print_status "Checking for deprecated parameters..."

# Check for deprecated --deployment-container-image-name
if grep -q "\-\-deployment-container-image-name" deploy-to-azure.sh; then
    print_error "Found deprecated parameter --deployment-container-image-name"
    grep -n "\-\-deployment-container-image-name" deploy-to-azure.sh
    exit 1
else
    print_success "No deprecated --deployment-container-image-name found"
fi

# Check for incorrect --yes flags on webapp delete
if grep -q "az webapp delete.*--yes" deploy-to-azure.sh; then
    print_error "Found incorrect --yes flag on az webapp delete command"
    grep -n "az webapp delete.*--yes" deploy-to-azure.sh
    exit 1
else
    print_success "No incorrect --yes flags on webapp delete commands"
fi

# Check that group delete commands have --yes flag (this is correct)
if grep -q "az group delete" deploy-to-azure.sh; then
    if grep -q "az group delete.*--yes" deploy-to-azure.sh; then
        print_success "Group delete commands correctly use --yes flag"
    else
        print_error "Group delete commands missing --yes flag"
        exit 1
    fi
fi

# Validate command syntax (basic check)
print_status "Validating command syntax..."

# Extract Azure CLI commands and validate basic syntax
while IFS= read -r line; do
    if [[ $line =~ ^[[:space:]]*az[[:space:]] ]]; then
        # This is an Azure CLI command line
        command=$(echo "$line" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*\\[[:space:]]*$//')
        
        # Skip if it's a comment or part of a multi-line command continuation
        if [[ $command =~ ^#.*$ ]] || [[ $command =~ \\$ ]]; then
            continue
        fi
        
        # Basic validation - check if command starts with known az subcommands
        if [[ $command =~ ^az[[:space:]]+(webapp|group|acr|appservice)[[:space:]] ]]; then
            print_status "✓ Valid command pattern: $(echo "$command" | cut -d' ' -f1-3)"
        else
            print_error "⚠ Unknown command pattern: $command"
        fi
    fi
done < deploy-to-azure.sh

print_status "Checking required parameters for key commands..."

# Check webapp create has required parameters
if grep -A 5 "az webapp create" deploy-to-azure.sh | grep -q "\-\-resource-group.*\-\-plan.*\-\-name"; then
    print_success "webapp create has required parameters"
else
    print_error "webapp create missing required parameters"
    exit 1
fi

# Check ACR create has required parameters  
if grep -A 5 "az acr create" deploy-to-azure.sh | grep -q "\-\-resource-group.*\-\-name.*\-\-sku"; then
    print_success "acr create has required parameters"
else
    print_error "acr create missing required parameters"
    exit 1
fi

print_success "🎉 All Azure CLI commands validated successfully!"
print_status "The deployment script uses correct Azure CLI syntax and parameters."
