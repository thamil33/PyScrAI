#!/usr/bin/env python
"""
Database initialization script for PyScrAI.

This script initializes the database and seeds it with initial data,
including all templates from the templates directory.

Usage:
    python -m pyscrai.scripts.init_db              # Interactive mode with menu
    python -m pyscrai.scripts.init_db --init       # Initialize without prompting
    python -m pyscrai.scripts.init_db --reset      # Reset without prompting (CAUTION!)
    python -m pyscrai.scripts.init_db --info       # Display database info only
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init()

# Add the project root to the path to enable imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_header(text: str) -> None:
    """Print a colorful header"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")

def print_success(text: str) -> None:
    """Print a success message"""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_warning(text: str) -> None:
    """Print a warning message"""
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")

def print_error(text: str) -> None:
    """Print an error message"""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def initialize_database_interactive():
    """Initialize database with interactive menu"""
    try:
        from pyscrai.databases.database import init_database, get_database_info, reset_database
        
        templates_dir = project_root / "pyscrai" / "templates"
        
        print_header("PyScrAI Database Initialization")
        print("This will initialize the database and seed it with initial data.")
        print("If the database already exists, existing data will be preserved.")
        print("Templates in the templates directory will be imported if they don't already exist.")
        
        print(f"\nTemplate directories that will be scanned:")
        print(f"  - Events:    {templates_dir / 'events'}")
        print(f"  - Agents:    {templates_dir / 'agents'}")
        print(f"  - Scenarios: {templates_dir / 'scenarios'}")
        
        choice = input("\nOptions:\n1. Initialize database (preserves existing data)\n2. Reset database (DELETES ALL DATA)\n3. Exit\n\nEnter choice (1-3): ")
        
        if choice == "1":
            print("\nInitializing database...")
            init_database()
            
            # Print database info after initialization
            db_info = get_database_info()
            print_header("PyScrAI Database Information")
            print(f"  Path: {db_info.get('database_path')}")
            print(f"  Exists: {db_info.get('database_exists')}")
            if "error" in db_info:
                print_error(f"  Error retrieving info: {db_info['error']}")
            if db_info.get('table_counts'):
                print("\n  Table Counts:")
                for table, count in sorted(db_info['table_counts'].items()):
                    print(f"    {table}: {count}")
            print("------------------------------------")
            
            print_success("Database initialization complete!")
            
        elif choice == "2":
            print_warning("\nWARNING: This will delete all existing data in the database!")
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() == "yes":
                reset_database()
                print_success("\nDatabase has been reset and reinitialized!")
            else:
                print("\nReset cancelled.")
        else:
            print("\nExiting without changes.")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        print_error(f"\nError: {e}")
        return False
        
    return True

def main():
    """Main entry point with command line parsing"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PyScrAI Database Initialization")
    parser.add_argument('--init', action='store_true', help='Initialize database without prompting')
    parser.add_argument('--reset', action='store_true', help='Reset database without prompting (WARNING: deletes all data)')
    parser.add_argument('--info', action='store_true', help='Display database information')
    
    args = parser.parse_args()
    
    try:
        from pyscrai.databases.database import init_database, get_database_info, reset_database
        
        # Process command line arguments
        if args.reset:
            print_warning("Resetting database without confirmation (--reset flag used)")
            reset_database(skip_confirmation=True)
            print_success("Database has been reset and reinitialized!")
        
        elif args.init:
            print("Initializing database without prompting (--init flag used)")
            init_database()
            print_success("Database initialization complete!")
        
        elif args.info:
            # Just show database info
            pass
        
        else:
            # No command line arguments, use interactive mode
            return 0 if initialize_database_interactive() else 1
        
        # Show database info if requested or after operations
        if args.info or args.init or args.reset:
            db_info = get_database_info()
            print_header("PyScrAI Database Information")
            print(f"  Path: {db_info.get('database_path')}")
            print(f"  Exists: {db_info.get('database_exists')}")
            if "error" in db_info:
                print_error(f"  Error retrieving info: {db_info['error']}")
            if db_info.get('table_counts'):
                print("\n  Table Counts:")
                for table, count in sorted(db_info['table_counts'].items()):
                    print(f"    {table}: {count}")
            print("------------------------------------")
            
        return 0
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print_error(f"\nError: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
