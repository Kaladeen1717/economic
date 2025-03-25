#!/usr/bin/env python3
"""
Module for retrieving booked invoice lines from e-conomic API.
"""
import argparse
import json
import os
import sys
import re
from datetime import datetime
from typing import Dict, List, Optional, Union
import requests

from auth import EconomicAuth, get_demo_auth, load_auth_from_file


class InvoiceLineRetriever:
    """
    Class to handle retrieving invoice lines from e-conomic API.
    """
    BASE_URL = "https://apis.e-conomic.com/q2capi/v4.0.0"
    BOOKED_LINES_ENDPOINT = "/invoices/booked/lines"
    
    def __init__(self, auth: EconomicAuth, company_name: Optional[str] = None):
        """
        Initialize with authentication.
        
        Args:
            auth: EconomicAuth instance for API authentication
            company_name: Optional company name for file naming
        """
        self.auth = auth
        self.company_name = company_name
    
    def get_all_invoice_lines(self, filter_params: Optional[str] = None, 
                             cursor: Optional[str] = None) -> Dict:
        """
        Retrieve all booked invoice lines, with optional filtering.
        Uses pagination with cursor to handle large datasets.
        
        Args:
            filter_params: Optional filter string for API
            cursor: Optional cursor for pagination
            
        Returns:
            Dictionary containing invoice line data and cursor for next page
        """
        url = f"{self.BASE_URL}{self.BOOKED_LINES_ENDPOINT}"
        
        # Build query parameters
        params = {}
        if filter_params:
            params["filter"] = filter_params
        if cursor:
            params["cursor"] = cursor
            
        # Make API request
        response = requests.get(
            url, 
            headers=self.auth.get_auth_headers(),
            params=params
        )
        
        # Raise exception if request failed
        response.raise_for_status()
        
        return response.json()
    
    def get_all_with_pagination(self, filter_params: Optional[str] = None) -> List[Dict]:
        """
        Get all invoice lines with automatic pagination handling.
        
        Args:
            filter_params: Optional filter string for API
            
        Returns:
            List of all invoice line data dictionaries
        """
        all_items = []
        next_cursor = None
        
        while True:
            # Get page of results
            response_data = self.get_all_invoice_lines(
                filter_params=filter_params, 
                cursor=next_cursor
            )
            
            # Add items to our collection
            if "items" in response_data and response_data["items"]:
                all_items.extend(response_data["items"])
            
            # Check for next page
            next_cursor = response_data.get("cursor")
            if not next_cursor:
                break
                
        return all_items
    
    def save_to_json(self, data: Union[List, Dict], filename: Optional[str] = None) -> str:
        """
        Save data to JSON file in the data_output directory.
        
        Args:
            data: Data to save
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Path to the saved file
        """
        # Create filename with timestamp if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Include company name in the filename if available
            if self.company_name:
                filename = f"invoice_lines_{self.company_name}_{timestamp}.json"
            else:
                filename = f"invoice_lines_{timestamp}.json"
        
        # Ensure filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
            
        # Build full path to output directory
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Full path to output file
        file_path = os.path.join(output_dir, filename)
        
        # Write data to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        return file_path


def get_auth_credentials_path(creds_filename: str) -> str:
    """
    Get the full path to the credentials file.
    
    If the file exists as provided, returns the path as-is.
    Otherwise, checks if the file exists in the authentication_schemas directory.
    
    Args:
        creds_filename: Name of or path to the credentials file
        
    Returns:
        Full path to the credentials file
    """
    # If the file exists as provided, use it
    if os.path.isfile(creds_filename):
        return creds_filename
    
    # Check if the file exists in the authentication_schemas directory
    auth_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "authentication_schemas")
    auth_path = os.path.join(auth_dir, creds_filename)
    
    # If the file exists in auth_dir, return that path
    if os.path.isfile(auth_path):
        return auth_path
    
    # Otherwise, just return the original path (which will likely cause a FileNotFoundError)
    return creds_filename


def extract_company_name(credentials_filename: str) -> Optional[str]:
    """
    Extract company name from credentials filename.
    
    Expected format: [company_name]_credentials.json
    
    Args:
        credentials_filename: Path to credentials file
        
    Returns:
        Company name or None if pattern doesn't match
    """
    # Extract just the filename part
    base_filename = os.path.basename(credentials_filename)
    
    # Use regex to extract company name
    match = re.match(r'(.+)_credentials\.json$', base_filename)
    if match:
        return match.group(1)
    return None


def list_available_credentials():
    """
    List all available credential files in the authentication_schemas directory.
    """
    auth_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "authentication_schemas")
    
    # List all JSON files in the directory
    if os.path.isdir(auth_dir):
        cred_files = [f for f in os.listdir(auth_dir) if f.endswith('.json')]
        if cred_files:
            print("\nAvailable credential files:")
            for file in cred_files:
                company = extract_company_name(file)
                if company:
                    print(f"  - {file} (Company: {company})")
                else:
                    print(f"  - {file}")
            print("\nUse with: python invoice_lines.py --creds-file FILENAME")
        else:
            print("\nNo credential files found in authentication_schemas directory.")
    else:
        print("\nAuthentication schemas directory not found.")


def parse_args():
    """Parse command line arguments."""
    # Special case handling for --list-creds
    if '--list-creds' in sys.argv and '--creds-file' not in sys.argv:
        # If just listing credentials, don't require --creds-file
        parser = argparse.ArgumentParser(description="Retrieve booked invoice lines from e-conomic API")
        parser.add_argument("--list-creds", action="store_true",
                         help="List available credential files in authentication_schemas directory")
        args, _ = parser.parse_known_args()
        if args.list_creds:
            return args
    
    # Normal argument parsing
    parser = argparse.ArgumentParser(description="Retrieve booked invoice lines from e-conomic API")
    
    # Authentication options
    auth_group = parser.add_argument_group("Authentication")
    auth_group.add_argument("--creds-file", required=True,
                           help="Path to credentials JSON file (looks in authentication_schemas directory by default)")
    auth_group.add_argument("--demo", action="store_true",
                           help="Use demo authentication instead of credentials file")
    auth_group.add_argument("--list-creds", action="store_true",
                           help="List available credential files in authentication_schemas directory")
    
    # Data retrieval options
    data_group = parser.add_argument_group("Data Retrieval")
    data_group.add_argument("--filter", help="Filter expression for API query")
    data_group.add_argument("--output", help="Output filename (default: timestamp-based filename)")
    
    return parser.parse_args()


def main():
    """Main function to retrieve and save invoice lines."""
    args = parse_args()
    
    # Only list credentials if requested
    if hasattr(args, 'list_creds') and args.list_creds and not hasattr(args, 'creds_file'):
        list_available_credentials()
        return 0
    
    try:
        # Extract company name for file naming
        company_name = extract_company_name(args.creds_file)
        
        # Get authentication
        if args.demo:
            # Override credentials file if demo is specified
            print("Using demo authentication")
            auth = get_demo_auth()
            # Add "demo" indicator to filenames, but preserve company name when available
            if not company_name:
                company_name = "demo"
            else:
                company_name = f"{company_name}_demo"
        else:
            # Require credentials file otherwise
            creds_path = get_auth_credentials_path(args.creds_file)
            print(f"Using credentials from file: {creds_path}")
            auth = load_auth_from_file(creds_path)
            if not auth:
                print(f"Could not load credentials from {creds_path}")
                return 1
        
        # Create retriever with company name
        retriever = InvoiceLineRetriever(auth, company_name)
        
        # Get all invoice lines with optional filter
        print("Retrieving booked invoice lines...")
        invoice_lines = retriever.get_all_with_pagination(filter_params=args.filter)
        
        # Save to file
        if invoice_lines:
            file_path = retriever.save_to_json(invoice_lines, filename=args.output)
            print(f"Retrieved {len(invoice_lines)} invoice lines")
            print(f"Data saved to: {file_path}")
        else:
            print("No invoice lines found")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 