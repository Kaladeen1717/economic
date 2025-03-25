#!/usr/bin/env python3
"""
Authentication module for e-conomic API.
Handles API tokens and authentication headers.
"""
import json
import os
from typing import Dict, Optional


class EconomicAuth:
    """
    Class to handle e-conomic API authentication.
    """
    def __init__(self, app_secret_token: str = None, agreement_grant_token: str = None):
        """
        Initialize authentication with tokens.
        
        Args:
            app_secret_token: Application secret token
            agreement_grant_token: Agreement grant token
        """
        # If tokens not provided, try to get from environment variables
        self.app_secret_token = app_secret_token or os.environ.get("ECONOMIC_APP_SECRET_TOKEN")
        self.agreement_grant_token = agreement_grant_token or os.environ.get("ECONOMIC_AGREEMENT_GRANT_TOKEN")
        
        # Validate tokens
        if not self.app_secret_token or not self.agreement_grant_token:
            raise ValueError(
                "API tokens are required. Provide them as arguments or set "
                "ECONOMIC_APP_SECRET_TOKEN and ECONOMIC_AGREEMENT_GRANT_TOKEN environment variables."
            )
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers required for API requests.
        
        Returns:
            Dictionary with authentication headers
        """
        return {
            "X-AppSecretToken": self.app_secret_token,
            "X-AgreementGrantToken": self.agreement_grant_token,
            "Content-Type": "application/json"
        }


def get_demo_auth() -> EconomicAuth:
    """
    Helper function to create demo authentication.
    According to API docs, the word 'demo' can be used for both tokens.
    
    Returns:
        EconomicAuth instance with demo credentials
    """
    return EconomicAuth(app_secret_token="demo", agreement_grant_token="demo")


def load_auth_from_file(credential_file: str) -> Optional[EconomicAuth]:
    """
    Load authentication from credentials JSON file.
    
    Args:
        credential_file: Path to credentials JSON file
        
    Returns:
        EconomicAuth instance with credentials from file or None if file not found
    """
    try:
        with open(credential_file, 'r', encoding='utf-8') as f:
            credentials = json.load(f)
            
        # Extract credentials from JSON
        economic_creds = credentials.get('economic_api', {})
        app_secret = economic_creds.get('app_secret_token')
        agreement_grant = economic_creds.get('agreement_grant_token')
        
        # Create auth object
        return EconomicAuth(
            app_secret_token=app_secret,
            agreement_grant_token=agreement_grant
        )
    except FileNotFoundError:
        print(f"Warning: Credentials file not found at {credential_file}")
        return None
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in credentials file {credential_file}")
        return None
    except Exception as e:
        print(f"Warning: Error loading credentials: {e}")
        return None 