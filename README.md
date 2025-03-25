# e_conomic ETL Project

This repository contains Python scripts for extracting, transforming, and loading data from e-conomic API endpoints.

## Setup

1. Make sure you have Python 3.6+ installed
2. Install dependencies: `pip install -r requirements.txt`
3. Create a credentials JSON file in `authentication_schemas/` (see template)

## Available Scripts

### 1. Retrieving Invoice Lines

The `invoice_lines.py` script retrieves invoice lines from the e-conomic API.

#### Usage

Basic usage:
```
python invoice_lines.py --creds-file [company_name]_credentials.json
```

With custom output filename:
```
python invoice_lines.py --creds-file [company_name]_credentials.json --output my_custom_filename.json
```

Using demo mode:
```
python invoice_lines.py --demo
```

List available credential files:
```
python invoice_lines.py --list-creds
```

#### Arguments

- `--creds-file`: Path to the credentials file (optional with --demo)
- `--output`: Custom output filename (default: timestamp-based filename)
- `--demo`: Use demo authentication instead of credentials file
- `--list-creds`: List available credential files

#### Output

The script outputs a JSON file in the `data_output/` directory with the naming convention:
```
invoice_lines_[company_name]_YYYYMMDD_HHMMSS.json
```

### 2. Retrieving Attached Documents

The `retrieve_single_attached_document.py` script allows retrieving attached documents from the e-conomic API.

#### Usage

Retrieve a specific document by its document number:
```
python retrieve_single_attached_document.py --creds-file [company_name]_credentials.json --document-number 12345678
```

Retrieve documents by voucher number:
```
python retrieve_single_attached_document.py --creds-file [company_name]_credentials.json --voucher-number 12345
```

List all available documents:
```
python retrieve_single_attached_document.py --creds-file [company_name]_credentials.json --list-all
```

#### Arguments

- `--creds-file`: Path to the credentials file (optional with --demo)
- `--document-number`: Specific document number to retrieve
- `--voucher-number`: Retrieve all documents with this voucher number
- `--list-all`: List all available documents
- `--download-pdf`: Download the PDF file for the document
- `--output-dir`: Directory to save PDFs (default: 'data_output/pdfs/')
- `--demo`: Use demo authentication instead of credentials file

#### Output

- Document metadata is saved as `attached_document_[company_name]_[document_number].json`
- PDF files (if requested) are saved as `attached_document_[company_name]_[document_number].pdf`
- Voucher search results are saved as `voucher_[company_name]_[voucher_number].json`

### 3. Retrieving Booked Entries

The `retrieve_all_booked_entries.py` script retrieves booked entries from the e-conomic API.

#### Usage

Basic usage with default date range (Jan 1, 2024 to today):
```
python retrieve_all_booked_entries.py --creds-file [company_name]_credentials.json
```

With custom date range:
```
python retrieve_all_booked_entries.py --creds-file [company_name]_credentials.json --start-date 2023-01-01 --end-date 2023-12-31
```

Using demo mode:
```
python retrieve_all_booked_entries.py --demo --start-date 2023-01-01 --end-date 2023-12-31
```

List available credential files:
```
python retrieve_all_booked_entries.py --list-creds
```

#### Arguments

- `--creds-file`: Path to the credentials file (optional with --demo)
- `--start-date`: Start date for entries retrieval (YYYY-MM-DD format, default: 2024-01-01)
- `--end-date`: End date for entries retrieval (YYYY-MM-DD format, default: today)
- `--filter`: Additional filter expression for API query
- `--output`: Custom output filename (default: timestamp-based filename)
- `--demo`: Use demo authentication instead of credentials file
- `--list-creds`: List available credential files

#### Output

The script outputs a JSON file in the `data_output/` directory with the naming convention:
```
booked_entries_[company_name]_YYYYMMDD_HHMMSS.json
```

## Authentication

The scripts use e-conomic API authentication with two tokens:
1. App Secret Token
2. Agreement Grant Token

These are stored in a credentials file in the `authentication_schemas/` directory with the naming convention:
```
[company_name]_credentials.json
```

Example credentials file format:
```json
{
  "app_secret_token": "your_app_secret_token",
  "agreement_grant_token": "your_agreement_grant_token"
}
```

## Demo Mode

All scripts support a demo mode which uses the e-conomic demo credentials. This is useful for testing without using real API credentials.

To use demo mode, simply add the `--demo` flag to any command:
```
python invoice_lines.py --demo
```