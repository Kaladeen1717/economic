#!/usr/bin/env python3
"""
Module for retrieving booked entries from e-conomic API.
"""
import argparse
import json
import os
import sys
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Union
import requests

from auth import EconomicAuth, get_demo_auth, load_auth_from_file


class BookedEntriesRetriever:
    """
    Class to handle retrieving booked entries from e-conomic API.
    """
    BASE_URL = "https://apis.e-conomic.com/bookedEntriesapi/v3.1.0"
    BOOKED_ENTRIES_ENDPOINT = "/booked-entries"
    
    def __init__(self, auth: EconomicAuth, company_name: Optional[str] = None):
        """
        Initialize with authentication.
        
        Args:
            auth: EconomicAuth instance for API authentication
            company_name: Optional company name for file naming
        """
        self.auth = auth
        self.company_name = company_name
        self.session = requests.Session()
    
    def get_all_booked_entries(self, filter_params: Optional[str] = None, 
                             cursor: Optional[str] = None) -> Dict:
        """
        Retrieve all booked entries, with optional filtering.
        Uses pagination with cursor to handle large datasets.
        
        Args:
            filter_params: Optional filter string for API
            cursor: Optional cursor for pagination
            
        Returns:
            Dictionary containing booked entries data and cursor for next page
        """
        url = f"{self.BASE_URL}{self.BOOKED_ENTRIES_ENDPOINT}"
        
        # Build query parameters
        params = {}
        if filter_params:
            params["filter"] = filter_params
        if cursor:
            params["cursor"] = cursor
            
        # Make API request
        response = self.session.get(
            url, 
            headers=self.auth.get_auth_headers(),
            params=params
        )
        
        # Raise exception if request failed
        response.raise_for_status()
        
        return response.json()
    
    def get_all_with_pagination(self, filter_params: Optional[str] = None) -> List[Dict]:
        """
        Get all booked entries with automatic pagination handling.
        
        Args:
            filter_params: Optional filter string for API
            
        Returns:
            List of all booked entries data dictionaries
        """
        all_items = []
        next_cursor = None
        
        while True:
            # Get page of results
            response_data = self.get_all_booked_entries(
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
                filename = f"booked_entries_{self.company_name}_{timestamp}.json"
            else:
                filename = f"booked_entries_{timestamp}.json"
        
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

    def __del__(self):
        """Cleanup method to ensure session is closed."""
        self.session.close()


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
            print("\nUse with: python retrieve_all_booked_entries.py --creds-file FILENAME")
        else:
            print("\nNo credential files found in authentication_schemas directory.")
    else:
        print("\nAuthentication schemas directory not found.")


def create_date_filter(start_date: str, end_date: str) -> str:
    """
    Create a filter string for date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Filter string for API query
    """
    return f"date$gte:{start_date}$and:date$lte:{end_date}"


def parse_args():
    """Parse command line arguments."""
    # Special case handling for --list-creds or --demo without --creds-file
    if ('--list-creds' in sys.argv and '--creds-file' not in sys.argv) or \
       ('--demo' in sys.argv and '--creds-file' not in sys.argv):
        # Create parser with optional creds-file for these cases
        parser = argparse.ArgumentParser(description="Retrieve booked entries from e-conomic API")
        parser.add_argument("--list-creds", action="store_true",
                         help="List available credential files in authentication_schemas directory")
        parser.add_argument("--demo", action="store_true",
                         help="Use demo authentication instead of credentials file")
        parser.add_argument("--start-date", default="2024-01-01",
                          help="Start date for entries retrieval (YYYY-MM-DD format, default: 2024-01-01)")
        parser.add_argument("--end-date", default=date.today().isoformat(),
                          help=f"End date for entries retrieval (YYYY-MM-DD format, default: today {date.today().isoformat()})")
        parser.add_argument("--filter", help="Additional filter expression for API query")
        parser.add_argument("--output", help="Output filename (default: timestamp-based filename)")
        parser.add_argument("--creds-file", help="Path to credentials JSON file (optional with --demo)")
        args = parser.parse_args()
        return args
    
    # Normal argument parsing with required --creds-file
    parser = argparse.ArgumentParser(description="Retrieve booked entries from e-conomic API")
    
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
    data_group.add_argument("--start-date", default="2024-01-01",
                           help="Start date for entries retrieval (YYYY-MM-DD format, default: 2024-01-01)")
    data_group.add_argument("--end-date", default=date.today().isoformat(),
                           help=f"End date for entries retrieval (YYYY-MM-DD format, default: today {date.today().isoformat()})")
    data_group.add_argument("--filter", help="Additional filter expression for API query")
    data_group.add_argument("--output", help="Output filename (default: timestamp-based filename)")
    
    return parser.parse_args()


def main():
    """Main function to retrieve and save booked entries."""
    args = parse_args()
    
    # Only list credentials if requested
    if hasattr(args, 'list_creds') and args.list_creds and not hasattr(args, 'creds_file'):
        list_available_credentials()
        return 0
    
    try:
        # Extract company name for file naming (if creds file provided)
        company_name = None
        if hasattr(args, 'creds_file') and args.creds_file:
            company_name = extract_company_name(args.creds_file)
        
        # Get authentication
        if args.demo:
            # Use demo authentication
            print("Using demo authentication")
            auth = get_demo_auth()
            # Use demo as company name if none provided
            company_name = "demo" if not company_name else f"{company_name}_demo"
        else:
            # Require credentials file
            if not hasattr(args, 'creds_file') or not args.creds_file:
                print("Error: Credentials file is required unless using --demo")
                return 1
                
            creds_path = get_auth_credentials_path(args.creds_file)
            print(f"Using credentials from file: {creds_path}")
            auth = load_auth_from_file(creds_path)
            if not auth:
                print(f"Could not load credentials from {creds_path}")
                return 1
        
        # Create retriever with company name
        retriever = BookedEntriesRetriever(auth, company_name)
        
        # Create date filter
        date_filter = create_date_filter(args.start_date, args.end_date)
        
        # Combine with additional filter if provided
        filter_expr = date_filter
        if args.filter:
            filter_expr = f"{date_filter}$and:{args.filter}"
        
        # Get all booked entries with date filter
        print(f"Retrieving booked entries from {args.start_date} to {args.end_date}...")
        booked_entries = retriever.get_all_with_pagination(filter_params=filter_expr)
        
        # Save to file
        if booked_entries:
            file_path = retriever.save_to_json(booked_entries, filename=args.output)
            print(f"Retrieved {len(booked_entries)} booked entries")
            print(f"Data saved to: {file_path}")
        else:
            print("No booked entries found")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 