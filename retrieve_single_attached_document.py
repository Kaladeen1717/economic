#!/usr/bin/env python3
"""
Module for retrieving attached documents from e-conomic API.
"""
import argparse
import json
import os
import sys
import re
from typing import Dict, List, Optional, Union
import requests

from auth import EconomicAuth, get_demo_auth, load_auth_from_file


class AttachedDocumentRetriever:
    """
    Class to handle retrieving attached documents from e-conomic API.
    """
    BASE_URL = "https://apis.e-conomic.com/documentsapi/v1.0.1"
    ATTACHED_DOCS_ENDPOINT = "/AttachedDocuments"
    
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
    
    def get_attached_document(self, document_number: int) -> Dict:
        """
        Retrieve a single attached document by its number.
        
        Args:
            document_number: Unique number identifier for the document
            
        Returns:
            Dictionary containing attached document data
        """
        url = f"{self.BASE_URL}{self.ATTACHED_DOCS_ENDPOINT}/{document_number}"
            
        # Make API request
        response = self.session.get(
            url, 
            headers=self.auth.get_auth_headers()
        )
        
        # Raise exception if request failed
        response.raise_for_status()
        
        return response.json()
    
    def get_attached_document_pdf(self, document_number: int) -> bytes:
        """
        Retrieve the PDF file for a single attached document.
        
        Args:
            document_number: Unique number identifier for the document
            
        Returns:
            Bytes containing the PDF file
        """
        url = f"{self.BASE_URL}{self.ATTACHED_DOCS_ENDPOINT}/{document_number}/pdf"
            
        # Make API request
        response = self.session.get(
            url, 
            headers=self.auth.get_auth_headers()
        )
        
        # Raise exception if request failed
        response.raise_for_status()
        
        return response.content
    
    def list_all_documents(self, filter_params: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Retrieve a list of all attached documents.
        
        Args:
            filter_params: Optional filter string for API
            limit: Maximum number of documents to retrieve
            
        Returns:
            List of dictionaries containing attached document data
        """
        url = f"{self.BASE_URL}{self.ATTACHED_DOCS_ENDPOINT}/paged"
        
        # Build query parameters
        params = {
            "pageSize": min(limit, 100)  # API limit is 100
        }
        if filter_params:
            params["filter"] = filter_params
            
        # Make API request
        response = self.session.get(
            url, 
            headers=self.auth.get_auth_headers(),
            params=params
        )
        
        # Raise exception if request failed
        response.raise_for_status()
        
        return response.json()
    
    def find_by_voucher_number(self, voucher_number: int, accounting_year: Optional[str] = None) -> List[Dict]:
        """
        Find attached documents by voucher number.
        
        Args:
            voucher_number: The voucher number to search for
            accounting_year: Optional accounting year parameter
            
        Returns:
            List of dictionaries containing matching attached documents
        """
        url = f"{self.BASE_URL}{self.ATTACHED_DOCS_ENDPOINT}/paged"
        
        # Build filter string
        # The API expects $ before operators in the filter, e.g. voucherNumber$eq:70492
        filter_string = f"voucherNumber$eq:{voucher_number}"
        
        # Add accounting year to filter if provided
        if accounting_year:
            filter_string = f"{filter_string}$and:accountingYear$eq:{accounting_year}"
        
        # Build query parameters
        params = {
            "pageSize": 100,  # Maximum allowed by API
            "filter": filter_string
        }
            
        # Make API request
        response = self.session.get(
            url, 
            headers=self.auth.get_auth_headers(),
            params=params
        )
        
        # Raise exception if request failed
        response.raise_for_status()
        
        return response.json()
    
    def save_document_info_to_json(self, data: Dict, filename: Optional[str] = None) -> str:
        """
        Save document metadata to JSON file in the data_output directory.
        
        Args:
            data: Document metadata to save (as newline-delimited JSON)
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Path to the saved file
        """
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename if not provided
        if not filename:
            doc_number = data.get("number", "unknown")
            # Include company name in the filename if available
            if self.company_name:
                filename = f"attached_document_{self.company_name}_{doc_number}.jsonl"
            else:
                filename = f"attached_document_{doc_number}.jsonl"
        
        # Ensure filename has .jsonl extension
        if filename.endswith('.json'):
            filename = filename[:-5] + '.jsonl'
        elif not filename.endswith('.jsonl'):
            filename += '.jsonl'
        
        # Full path to output file
        file_path = os.path.join(output_dir, filename)
        
        # Write data to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data) + '\n')
            
        return file_path
    
    def save_document_pdf(self, document_number: int, data: bytes, filename: Optional[str] = None) -> str:
        """
        Save document PDF to file in the data_output directory.
        
        Args:
            document_number: Document number for naming
            data: PDF binary data to save
            filename: Optional filename, defaults to document-number-based name
            
        Returns:
            Path to the saved file
        """
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename if not provided
        if not filename:
            # Include company name in the filename if available
            if self.company_name:
                filename = f"attached_document_{self.company_name}_{document_number}.pdf"
            else:
                filename = f"attached_document_{document_number}.pdf"
        
        # Ensure filename has .pdf extension
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Full path to output file
        file_path = os.path.join(output_dir, filename)
        
        # Write binary data to file
        with open(file_path, 'wb') as f:
            f.write(data)
            
        return file_path
    
    def save_documents_list_to_json(self, data: List[Dict], filename: Optional[str] = None) -> str:
        """
        Save a list of documents to JSON file in the data_output directory.
        
        Args:
            data: List of document data to save (as newline-delimited JSON)
            filename: Optional filename, defaults to company-based name
            
        Returns:
            Path to the saved file
        """
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename if not provided
        if not filename:
            # Include company name in the filename if available
            if self.company_name:
                filename = f"attached_documents_list_{self.company_name}.jsonl"
            else:
                filename = f"attached_documents_list.jsonl"
        
        # Ensure filename has .jsonl extension
        if filename.endswith('.json'):
            filename = filename[:-5] + '.jsonl'
        elif not filename.endswith('.jsonl'):
            filename += '.jsonl'
        
        # Full path to output file
        file_path = os.path.join(output_dir, filename)
        
        # Write data to file
        with open(file_path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
            
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
            print("\nUse with: python retrieve_single_attached_document.py --creds-file FILENAME --document-number NUMBER")
        else:
            print("\nNo credential files found in authentication_schemas directory.")
    else:
        print("\nAuthentication schemas directory not found.")


def parse_args():
    """Parse command line arguments."""
    # Special case handling for --list-creds
    if '--list-creds' in sys.argv and '--creds-file' not in sys.argv:
        # If just listing credentials, don't require --creds-file
        parser = argparse.ArgumentParser(description="Retrieve attached documents from e-conomic API")
        parser.add_argument("--list-creds", action="store_true",
                         help="List available credential files in authentication_schemas directory")
        args, _ = parser.parse_known_args()
        if args.list_creds:
            return args
    
    # Normal argument parsing
    parser = argparse.ArgumentParser(description="Retrieve attached documents from e-conomic API")
    
    # Authentication options
    auth_group = parser.add_argument_group("Authentication")
    auth_group.add_argument("--creds-file", required=True,
                           help="Path to credentials JSON file (looks in authentication_schemas directory by default)")
    auth_group.add_argument("--demo", action="store_true",
                           help="Use demo authentication instead of credentials file")
    auth_group.add_argument("--list-creds", action="store_true",
                           help="List available credential files in authentication_schemas directory")
    
    # Document options
    doc_group = parser.add_argument_group("Document Retrieval")
    doc_group.add_argument("--document-number", type=int,
                          help="Number of the attached document to retrieve")
    doc_group.add_argument("--voucher-number", type=int,
                          help="Search for documents by voucher number")
    doc_group.add_argument("--accounting-year", 
                          help="Accounting year for voucher search (optional)")
    doc_group.add_argument("--get-pdf", action="store_true",
                          help="Also retrieve and save the PDF file for the document")
    doc_group.add_argument("--output", help="Output filename (default: document-number-based filename)")
    doc_group.add_argument("--list-docs", action="store_true",
                          help="List all available attached documents")
    doc_group.add_argument("--filter", help="Filter expression for API query when listing documents")
    doc_group.add_argument("--limit", type=int, default=100,
                          help="Maximum number of documents to retrieve when listing (default: 100)")
    
    args = parser.parse_args()
    
    # Validate args
    if not (args.list_docs or args.document_number or args.voucher_number):
        parser.error("Either --document-number, --voucher-number, or --list-docs is required")
    
    return args


def main():
    """Main function to retrieve and save attached documents."""
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
        retriever = AttachedDocumentRetriever(auth, company_name)
        
        # Find documents by voucher number if requested
        if args.voucher_number:
            print(f"Searching for documents with voucher number {args.voucher_number}...")
            try:
                documents = retriever.find_by_voucher_number(
                    args.voucher_number, 
                    accounting_year=args.accounting_year
                )
                
                if documents:
                    # Create filename for voucher document list
                    if not args.output:
                        if company_name:
                            voucher_filename = f"voucher_{company_name}_{args.voucher_number}.jsonl"
                        else:
                            voucher_filename = f"voucher_{args.voucher_number}.jsonl"
                    else:
                        voucher_filename = args.output
                    
                    # Save documents to file
                    file_path = retriever.save_documents_list_to_json(documents, filename=voucher_filename)
                    print(f"Found {len(documents)} document(s) for voucher #{args.voucher_number}")
                    print(f"Document list saved to: {file_path}")
                    
                    # Print the found documents
                    print("\nAttached documents for this voucher:")
                    for doc in documents:
                        print(f"  - Document #{doc.get('number')}: {doc.get('note', 'No note')}")
                    
                    # If only one document was found and --get-pdf was specified, get the PDF
                    if len(documents) == 1 and args.get_pdf:
                        doc_number = documents[0].get('number')
                        print(f"\nRetrieving PDF for document #{doc_number}...")
                        pdf_data = retriever.get_attached_document_pdf(doc_number)
                        
                        # Save PDF to file
                        pdf_filename = f"voucher_{company_name}_{args.voucher_number}.pdf" if company_name else f"voucher_{args.voucher_number}.pdf"
                        pdf_path = retriever.save_document_pdf(doc_number, pdf_data, filename=pdf_filename)
                        print(f"PDF file saved to: {pdf_path}")
                        
                    # If multiple documents were found and --get-pdf was specified, prompt user
                    elif len(documents) > 1 and args.get_pdf:
                        print("\nMultiple documents found. To retrieve a specific PDF, run the command again with --document-number instead of --voucher-number.")
                        
                else:
                    print(f"No documents found for voucher #{args.voucher_number}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"Error: No documents found for voucher #{args.voucher_number}")
                else:
                    raise
        
        # List all documents if requested
        elif args.list_docs:
            print(f"Retrieving list of attached documents (limit: {args.limit})...")
            try:
                documents = retriever.list_all_documents(filter_params=args.filter, limit=args.limit)
                
                if documents:
                    # Save documents to file
                    file_path = retriever.save_documents_list_to_json(documents, filename=args.output)
                    print(f"Retrieved {len(documents)} attached documents")
                    print(f"Document list saved to: {file_path}")
                    
                    # Print sample of documents
                    print("\nAvailable document numbers:")
                    for doc in documents[:10]:  # Show first 10
                        print(f"  - {doc.get('number')}: {doc.get('note', 'No note')}")
                    
                    if len(documents) > 10:
                        print(f"  ... and {len(documents) - 10} more (see the saved JSON file for complete list)")
                else:
                    print("No attached documents found")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print("Error: No attached documents found")
                else:
                    raise
        
        # Get single document if requested
        elif args.document_number:
            # Get document info
            print(f"Retrieving attached document #{args.document_number}...")
            document_data = retriever.get_attached_document(args.document_number)
            
            # Save document info to file
            file_path = retriever.save_document_info_to_json(document_data, filename=args.output)
            print(f"Document info saved to: {file_path}")
            
            # Get PDF if requested
            if args.get_pdf:
                print("Retrieving PDF file...")
                pdf_data = retriever.get_attached_document_pdf(args.document_number)
                
                # Save PDF to file
                pdf_filename = args.output.replace('.jsonl', '.pdf') if args.output else None
                pdf_path = retriever.save_document_pdf(args.document_number, pdf_data, filename=pdf_filename)
                print(f"PDF file saved to: {pdf_path}")
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Error: Document #{args.document_number} not found")
        elif e.response.status_code == 401:
            print("Error: Unauthorized - Invalid API credentials")
        elif e.response.status_code == 403:
            print("Error: Forbidden - Insufficient permissions")
        else:
            print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 