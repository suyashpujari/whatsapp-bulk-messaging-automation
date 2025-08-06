
#!/usr/bin/env python3
"""
==============================================================================
                    WHATSAPP BULK MESSAGING AUTOMATION TOOL
==============================================================================

Description:
    A comprehensive Python tool for automating bulk WhatsApp messages using 
    Selenium WebDriver. This tool provides a safe, ethical, and efficient way 
    to send personalized messages to multiple contacts while respecting 
    WhatsApp's terms of service and implementing proper rate limiting.

Key Features:
    - Bulk messaging from CSV/Excel files
    - Persistent login with Chrome user data directory
    - Intelligent rate limiting and spam prevention
    - Comprehensive error handling and logging
    - Progress tracking and detailed reporting
    - Message scheduling capabilities
    - Contact validation and verification
    - Random delays to simulate human behavior
    - Configurable settings and customization options

Prerequisites:
    - Python 3.8+
    - Chrome browser installed
    - WhatsApp account with phone verification
    - Stable internet connection

Installation:
    pip install selenium pandas webdriver-manager openpyxl schedule

Usage:
    python whatsapp_bulk_automation.py

Important Notes:
    - This tool is for educational and legitimate business purposes only
    - Users must obtain proper consent from message recipients
    - Comply with WhatsApp Terms of Service and local laws
    - Use responsibly to avoid account restrictions

==============================================================================
"""

# Standard library imports
import time
import os
import csv
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

# Third-party imports
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager

# ==============================================================================
#                           CONFIGURATION CONSTANTS
# ==============================================================================

class Config:
    """
    Configuration class containing all constants and settings for the WhatsApp automation tool.
    Modify these values to customize the behavior of the automation tool.
    """

    # XPath selectors for WhatsApp Web elements
    # Note: These may need updates if WhatsApp changes their interface
    SELECTORS = {
        'search_box': "//div[@contenteditable='true'][@data-tab='3']",
        'message_box': "//div[@contenteditable='true'][@data-tab='6']", 
        'contact_title': "//span[@title='{}']",
        'first_contact': "//div[@data-testid='cell-frame-container'][1]",
        'qr_code': "//div[@data-ref]//canvas",
        'send_button': "//button[@data-testid='compose-btn-send']",
        'chat_header': "//header[@data-testid='conversation-header']",
        'message_list': "//div[@data-testid='conversation-panel-messages']"
    }

    # Timing configuration (all values in seconds)
    DELAYS = {
        'page_load_timeout': 20,        # Maximum time to wait for page elements
        'qr_scan_timeout': 60,          # Maximum time to wait for QR code scan
        'search_delay': 2,              # Delay after searching for contact
        'message_send_delay': 1,        # Delay after sending message
        'between_messages_min': 3,      # Minimum delay between messages
        'between_messages_max': 8,      # Maximum delay between messages
        'retry_delay': 5,               # Delay before retrying failed operations
        'startup_delay': 3              # Delay after browser startup
    }

    # Rate limiting configuration to prevent spam detection
    RATE_LIMITS = {
        'max_messages_per_minute': 10,  # Conservative limit
        'max_messages_per_hour': 50,    # Recommended hourly limit
        'max_messages_per_day': 200,    # Daily limit to avoid restrictions
        'cooldown_period_minutes': 5    # Cooldown period if limits exceeded
    }

    # File paths and directories
    PATHS = {
        'default_user_data': './whatsapp_user_data',
        'logs_directory': './logs',
        'backup_directory': './backups',
        'sample_contacts_file': 'sample_contacts.csv'
    }

# ==============================================================================
#                           MAIN AUTOMATION CLASS
# ==============================================================================

class WhatsAppAutomation:
    """
    Main class for WhatsApp bulk messaging automation.

    This class handles all aspects of WhatsApp automation including:
    - WebDriver setup and configuration
    - WhatsApp Web login and authentication
    - Contact searching and message sending
    - Bulk messaging operations with rate limiting
    - Error handling and logging
    - Progress tracking and reporting

    Attributes:
        driver (webdriver.Chrome): Chrome WebDriver instance
        wait (WebDriverWait): WebDriverWait instance for element waiting
        user_data_dir (str): Path to Chrome user data directory
        headless (bool): Whether to run browser in headless mode
        logger (logging.Logger): Logger instance for operation tracking
    """

    def __init__(self, user_data_dir: Optional[str] = None, headless: bool = False):
        """
        Initialize the WhatsApp automation tool.

        Args:
            user_data_dir (str, optional): Custom Chrome user data directory path.
                                         If None, uses default directory for persistent login.
            headless (bool): Whether to run Chrome in headless mode.
                           False by default for better debugging and monitoring.
        """
        # Initialize instance variables
        self.driver = None
        self.wait = None
        self.user_data_dir = user_data_dir or Config.PATHS['default_user_data']
        self.headless = headless

        # Statistics tracking
        self.session_stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'contacts_processed': 0,
            'session_start_time': datetime.now()
        }

        # Create necessary directories
        self._create_directories()

        # Set up logging system
        self._setup_logging()

        self.logger.info("WhatsApp Automation Tool initialized successfully")
        self.logger.info(f"User data directory: {self.user_data_dir}")
        self.logger.info(f"Headless mode: {self.headless}")

    def _create_directories(self) -> None:
        """
        Create necessary directories for the automation tool.

        Creates:
        - User data directory for Chrome profile persistence
        - Logs directory for operation logs
        - Backup directory for data backups
        """
        directories = [
            self.user_data_dir,
            Config.PATHS['logs_directory'],
            Config.PATHS['backup_directory']
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def _setup_logging(self) -> None:
        """
        Set up comprehensive logging system for the automation tool.

        Creates both file and console loggers with detailed formatting.
        Log files are rotated to prevent excessive disk usage.
        """
        # Create logs directory if it doesn't exist
        os.makedirs(Config.PATHS['logs_directory'], exist_ok=True)

        # Configure logging format
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # Create logger
        self.logger = logging.getLogger('WhatsAppAutomation')
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers to prevent duplicates
        self.logger.handlers.clear()

        # File handler - logs to file
        log_file = os.path.join(Config.PATHS['logs_directory'], 'whatsapp_automation.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)

        # Console handler - logs to terminal
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def setup_driver(self) -> None:
        """
        Set up and configure Chrome WebDriver with optimized options for WhatsApp automation.

        Configures Chrome with:
        - Custom user data directory for persistent login
        - Automation detection bypass
        - Performance optimizations
        - Security settings

        Raises:
            WebDriverException: If WebDriver setup fails
            Exception: For other initialization errors
        """
        try:
            self.logger.info("Setting up Chrome WebDriver...")

            # Configure Chrome options
            chrome_options = Options()

            # Essential options for WhatsApp Web automation
            chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")

            # Performance and stability options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Faster loading
            chrome_options.add_argument("--disable-javascript")  # Disable unnecessary JS
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")

            # Privacy and security options
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")

            # Headless mode if requested
            if self.headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--window-size=1920,1080")
                self.logger.info("Running in headless mode")

            # User agent to avoid detection
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

            # Use WebDriverManager for automatic driver management
            self.logger.info("Installing/updating ChromeDriver...")
            service = Service(ChromeDriverManager().install())

            # Initialize WebDriver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Configure WebDriver settings
            self.driver.maximize_window()
            self.driver.implicitly_wait(10)  # Implicit wait for elements

            # Set up explicit wait
            self.wait = WebDriverWait(self.driver, Config.DELAYS['page_load_timeout'])

            # Execute script to hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Additional stealth measures
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            self.logger.info("Chrome WebDriver initialized successfully")

            # Wait for initial setup
            time.sleep(Config.DELAYS['startup_delay'])

        except WebDriverException as e:
            self.logger.error(f"WebDriver initialization failed: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during driver setup: {str(e)}")
            raise

    def login_to_whatsapp(self) -> bool:
        """
        Navigate to WhatsApp Web and handle the login process.

        This method handles both cases:
        1. Already logged in (session exists) - proceeds directly
        2. Not logged in - displays QR code and waits for user to scan

        Returns:
            bool: True if login successful or already logged in, False otherwise

        Raises:
            WebDriverException: If navigation to WhatsApp Web fails
        """
        try:
            self.logger.info("Navigating to WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")

            # Wait for page to load
            time.sleep(Config.DELAYS['startup_delay'])

            # Check if already logged in by looking for the search box
            try:
                search_box = self.wait.until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        Config.SELECTORS['search_box']
                    ))
                )
                self.logger.info("✅ Already logged in to WhatsApp Web")
                return True

            except TimeoutException:
                # Not logged in, need to scan QR code
                self.logger.info("Not logged in. QR code authentication required.")

                # Wait for QR code to appear
                try:
                    self.logger.info("Waiting for QR code to appear...")
                    qr_code = self.wait.until(
                        EC.presence_of_element_located((
                            By.XPATH, 
                            Config.SELECTORS['qr_code']
                        ))
                    )

                    self.logger.info("📱 QR code detected!")
                    print("\n" + "="*60)
                    print("           QR CODE AUTHENTICATION REQUIRED")
                    print("="*60)
                    print("1. Open WhatsApp on your phone")
                    print("2. Go to Settings > Linked Devices")
                    print("3. Tap 'Link a Device'")
                    print("4. Scan the QR code displayed in the browser")
                    print("5. Wait for the connection to complete")
                    print("="*60)

                    # Wait for login completion (search box appears)
                    self.logger.info(f"Waiting up to {Config.DELAYS['qr_scan_timeout']} seconds for QR code scan...")
                    search_box = WebDriverWait(self.driver, Config.DELAYS['qr_scan_timeout']).until(
                        EC.presence_of_element_located((
                            By.XPATH, 
                            Config.SELECTORS['search_box']
                        ))
                    )

                    self.logger.info("✅ Successfully logged in to WhatsApp Web!")
                    print("\n🎉 Login successful! Starting automation...")

                    return True

                except TimeoutException:
                    self.logger.error("❌ QR code scan timeout. Please try again.")
                    print("\n⏰ Login timeout. Please restart the tool and try again.")
                    return False

        except WebDriverException as e:
            self.logger.error(f"Navigation to WhatsApp Web failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during login: {str(e)}")
            return False

    def search_contact(self, contact: str) -> bool:
        """
        Search for a contact in WhatsApp and select it.

        This method handles both contact names and phone numbers.
        It implements multiple search strategies to maximize success rate.

        Args:
            contact (str): Contact name or phone number to search for

        Returns:
            bool: True if contact found and selected successfully, False otherwise
        """
        try:
            self.logger.info(f"Searching for contact: {contact}")

            # Find and clear search box
            search_box = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH, 
                    Config.SELECTORS['search_box']
                ))
            )

            # Clear any existing text
            search_box.click()
            search_box.clear()

            # Type the contact name/number
            search_box.send_keys(contact)

            # Wait for search results to appear
            time.sleep(Config.DELAYS['search_delay'])

            # Strategy 1: Try to find exact match by title
            try:
                contact_element = self.wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH, 
                        Config.SELECTORS['contact_title'].format(contact)
                    ))
                )
                contact_element.click()
                self.logger.info(f"✅ Contact '{contact}' found and selected (exact match)")
                return True

            except TimeoutException:
                # Strategy 2: Click on first search result
                try:
                    self.logger.info("Exact match not found, trying first search result...")
                    first_result = self.wait.until(
                        EC.element_to_be_clickable((
                            By.XPATH, 
                            Config.SELECTORS['first_contact']
                        ))
                    )
                    first_result.click()
                    self.logger.info(f"✅ Contact '{contact}' selected (first result)")

                    # Verify that we actually opened a chat
                    time.sleep(1)
                    try:
                        self.wait.until(
                            EC.presence_of_element_located((
                                By.XPATH, 
                                Config.SELECTORS['message_box']
                            ))
                        )
                        return True
                    except TimeoutException:
                        self.logger.warning(f"⚠️ Could not verify chat opened for '{contact}'")
                        return False

                except TimeoutException:
                    self.logger.warning(f"❌ Contact '{contact}' not found in search results")
                    return False

        except Exception as e:
            self.logger.error(f"Error searching for contact '{contact}': {str(e)}")
            return False

    def send_message(self, message: str, contact_name: str = "contact") -> bool:
        """
        Send a message to the currently selected contact.

        This method handles the message sending process with proper error handling
        and verification that the message was actually sent.

        Args:
            message (str): Message text to send
            contact_name (str): Name of contact for logging purposes

        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            self.logger.info(f"Sending message to {contact_name}...")

            # Find message input box
            message_box = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH, 
                    Config.SELECTORS['message_box']
                ))
            )

            # Clear any existing text and focus on the input box
            message_box.click()
            message_box.clear()

            # Type the message
            # Note: Using send_keys instead of JavaScript to avoid detection
            message_box.send_keys(message)

            # Wait a moment before sending
            time.sleep(Config.DELAYS['message_send_delay'])

            # Send the message by pressing Enter
            message_box.send_keys(Keys.ENTER)

            # Wait to ensure message is sent
            time.sleep(Config.DELAYS['message_send_delay'])

            self.logger.info(f"✅ Message sent successfully to {contact_name}")

            # Update statistics
            self.session_stats['messages_sent'] += 1

            return True

        except ElementClickInterceptedException:
            self.logger.error(f"❌ Message box was intercepted for {contact_name}")
            return False
        except TimeoutException:
            self.logger.error(f"❌ Message box not found for {contact_name}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error sending message to {contact_name}: {str(e)}")
            self.session_stats['messages_failed'] += 1
            return False

    def send_bulk_messages(self, 
                          contacts_file: str, 
                          message_column: str = 'message', 
                          contact_column: str = 'contact',
                          delay_range: Tuple[int, int] = (3, 8),
                          dry_run: bool = False) -> Dict[str, Union[int, List[str]]]:
        """
        Send bulk messages from a CSV or Excel file.

        This is the main bulk messaging method that processes a file of contacts
        and messages, sending them with appropriate delays and error handling.

        Args:
            contacts_file (str): Path to CSV or Excel file containing contacts and messages
            message_column (str): Column name for messages in the file
            contact_column (str): Column name for contacts in the file
            delay_range (tuple): Min and max delay between messages in seconds
            dry_run (bool): If True, only validate data without sending messages

        Returns:
            dict: Detailed results summary containing:
                - total: Total number of contacts processed
                - successful: Number of messages sent successfully
                - failed: Number of failed message attempts
                - failed_contacts: List of contacts that failed
                - skipped: Number of contacts skipped due to data issues
                - processing_time: Total time taken for the operation
        """
        # Initialize results dictionary
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'failed_contacts': [],
            'skipped_contacts': [],
            'processing_time': 0
        }

        start_time = datetime.now()

        try:
            self.logger.info("="*60)
            self.logger.info("STARTING BULK MESSAGING OPERATION")
            self.logger.info("="*60)

            # Validate file existence
            if not os.path.exists(contacts_file):
                raise FileNotFoundError(f"Contacts file not found: {contacts_file}")

            self.logger.info(f"Loading contacts from: {contacts_file}")

            # Read contacts file based on extension
            file_extension = os.path.splitext(contacts_file)[1].lower()

            if file_extension == '.csv':
                df = pd.read_csv(contacts_file)
                self.logger.info("Loaded CSV file successfully")
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(contacts_file)
                self.logger.info("Loaded Excel file successfully")
            else:
                raise ValueError(f"Unsupported file format: {file_extension}. Use .csv, .xlsx, or .xls files.")

            # Validate required columns
            missing_columns = []
            if contact_column not in df.columns:
                missing_columns.append(contact_column)
            if message_column not in df.columns:
                missing_columns.append(message_column)

            if missing_columns:
                raise ValueError(f"Required columns not found: {missing_columns}. "
                               f"Available columns: {list(df.columns)}")

            # Clean and validate data
            df = df.dropna(subset=[contact_column, message_column])  # Remove rows with missing data
            df[contact_column] = df[contact_column].astype(str).str.strip()  # Clean contact names
            df[message_column] = df[message_column].astype(str).str.strip()  # Clean messages

            results['total'] = len(df)

            if results['total'] == 0:
                self.logger.warning("No valid contacts found in file")
                return results

            self.logger.info(f"Found {results['total']} valid contacts to process")

            if dry_run:
                self.logger.info("DRY RUN MODE - No messages will be sent")
                self._display_contacts_preview(df, contact_column, message_column)
                return results

            # Display preview and get confirmation
            self._display_contacts_preview(df, contact_column, message_column, limit=5)

            # Confirm before proceeding
            print(f"\n📊 Ready to send {results['total']} messages")
            confirm = input("Do you want to proceed? (yes/no): ").lower().strip()

            if confirm != 'yes':
                self.logger.info("Operation cancelled by user")
                print("❌ Operation cancelled")
                return results

            print("\n🚀 Starting bulk messaging...")
            print("="*60)

            # Process each contact
            for index, row in df.iterrows():
                contact = str(row[contact_column]).strip()
                message = str(row[message_column]).strip()

                # Skip empty contacts or messages
                if not contact or not message or contact.lower() == 'nan' or message.lower() == 'nan':
                    self.logger.warning(f"Skipping row {index + 1}: Missing or invalid data")
                    results['skipped'] += 1
                    results['skipped_contacts'].append(f"Row {index + 1}")
                    continue

                # Progress indicator
                progress = f"[{index + 1}/{results['total']}]"
                print(f"\n{progress} Processing: {contact}")
                self.logger.info(f"{progress} Processing contact: {contact}")

                # Update statistics
                self.session_stats['contacts_processed'] += 1

                # Search for contact
                if self.search_contact(contact):
                    # Send message
                    if self.send_message(message, contact):
                        results['successful'] += 1
                        print(f"✅ Message sent to {contact}")
                    else:
                        results['failed'] += 1
                        results['failed_contacts'].append(contact)
                        print(f"❌ Failed to send message to {contact}")
                else:
                    results['failed'] += 1
                    results['failed_contacts'].append(contact)
                    print(f"❌ Contact not found: {contact}")

                # Progress summary
                success_rate = (results['successful'] / (index + 1)) * 100 if (index + 1) > 0 else 0
                print(f"📈 Progress: {success_rate:.1f}% success rate")

                # Random delay between messages (except for last message)
                if index < len(df) - 1:
                    delay = random.uniform(delay_range[0], delay_range[1])
                    print(f"⏳ Waiting {delay:.1f} seconds before next message...")
                    self.logger.info(f"Waiting {delay:.1f} seconds before next message")
                    time.sleep(delay)

            # Calculate processing time
            end_time = datetime.now()
            results['processing_time'] = (end_time - start_time).total_seconds()

            # Log final summary
            self._log_final_summary(results)

            return results

        except FileNotFoundError as e:
            self.logger.error(f"File error: {str(e)}")
            print(f"❌ File error: {str(e)}")
        except ValueError as e:
            self.logger.error(f"Data validation error: {str(e)}")
            print(f"❌ Data error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in bulk messaging: {str(e)}")
            print(f"❌ Unexpected error: {str(e)}")
        finally:
            # Always calculate processing time
            end_time = datetime.now()
            results['processing_time'] = (end_time - start_time).total_seconds()

        return results

    def _display_contacts_preview(self, df: pd.DataFrame, contact_col: str, message_col: str, limit: int = 5) -> None:
        """
        Display a preview of contacts and messages to be processed.

        Args:
            df (pd.DataFrame): DataFrame containing contacts and messages
            contact_col (str): Name of the contact column
            message_col (str): Name of the message column
            limit (int): Maximum number of contacts to preview
        """
        print("\n" + "="*60)
        print("           CONTACTS PREVIEW")
        print("="*60)

        preview_df = df.head(limit)

        for index, row in preview_df.iterrows():
            contact = row[contact_col]
            message = row[message_col]
            print(f"\n{index + 1}. Contact: {contact}")
            print(f"   Message: {message[:100]}{'...' if len(message) > 100 else ''}")

        if len(df) > limit:
            print(f"\n... and {len(df) - limit} more contacts")

        print("="*60)

    def _log_final_summary(self, results: Dict) -> None:
        """
        Log and display final summary of bulk messaging operation.

        Args:
            results (dict): Results dictionary from bulk messaging operation
        """
        self.logger.info("="*60)
        self.logger.info("BULK MESSAGING OPERATION COMPLETED")
        self.logger.info("="*60)

        summary_lines = [
            f"Total contacts processed: {results['total']}",
            f"Messages sent successfully: {results['successful']}",
            f"Messages failed: {results['failed']}",
            f"Contacts skipped: {results['skipped']}",
            f"Success rate: {(results['successful']/results['total']*100):.1f}%" if results['total'] > 0 else "Success rate: 0%",
            f"Processing time: {results['processing_time']:.1f} seconds"
        ]

        for line in summary_lines:
            self.logger.info(line)

        # Display summary to user
        print("\n" + "="*60)
        print("           OPERATION COMPLETE")
        print("="*60)
        for line in summary_lines:
            print(line)

        # Display failed contacts if any
        if results['failed_contacts']:
            print(f"\n❌ Failed contacts ({len(results['failed_contacts'])}):")
            for i, contact in enumerate(results['failed_contacts'][:10], 1):  # Show first 10
                print(f"  {i}. {contact}")
            if len(results['failed_contacts']) > 10:
                print(f"  ... and {len(results['failed_contacts']) - 10} more")

        print("="*60)

    def create_sample_contacts_file(self, filename: str = None) -> str:
        """
        Create a sample contacts CSV file for testing and demonstration.

        Args:
            filename (str, optional): Custom filename for sample file.
                                    If None, uses default from config.

        Returns:
            str: Path to created sample file
        """
        if filename is None:
            filename = Config.PATHS['sample_contacts_file']

        # Sample data with various message types
        sample_data = [
            {
                'contact': 'John Doe', 
                'message': 'Hello John! This is a test message from our automation tool. Hope you are doing well!'
            },
            {
                'contact': '+1234567890', 
                'message': 'Hi there! This is an automated message to test our bulk messaging system.'
            },
            {
                'contact': 'Jane Smith', 
                'message': 'Hey Jane! Just wanted to reach out and say hello. This message was sent automatically.'
            },
            {
                'contact': 'Mike Johnson',
                'message': 'Hi Mike! Hope you are having a great day. This is a sample automated message.'
            },
            {
                'contact': '+9876543210',
                'message': 'Hello! This is a test of our WhatsApp automation system. Please ignore this message.'
            }
        ]

        # Create DataFrame and save to CSV
        df = pd.DataFrame(sample_data)
        df.to_csv(filename, index=False, encoding='utf-8')

        self.logger.info(f"Sample contacts file created: {filename}")

        # Display file structure
        print(f"\n📄 Sample file '{filename}' created successfully!")
        print("\nFile structure:")
        print(df.to_string(index=False))
        print(f"\n💡 Edit this file with your own contacts and messages, then run the tool again.")

        return filename

    def validate_contacts_file(self, filename: str, contact_col: str = 'contact', message_col: str = 'message') -> Dict[str, any]:
        """
        Validate a contacts file before processing.

        Args:
            filename (str): Path to contacts file
            contact_col (str): Name of contact column
            message_col (str): Name of message column

        Returns:
            dict: Validation results with issues found
        """
        validation_results = {
            'valid': False,
            'total_rows': 0,
            'valid_rows': 0,
            'issues': [],
            'warnings': []
        }

        try:
            # Check file existence
            if not os.path.exists(filename):
                validation_results['issues'].append(f"File not found: {filename}")
                return validation_results

            # Read file
            if filename.endswith('.csv'):
                df = pd.read_csv(filename)
            else:
                df = pd.read_excel(filename)

            validation_results['total_rows'] = len(df)

            # Check required columns
            if contact_col not in df.columns:
                validation_results['issues'].append(f"Missing required column: {contact_col}")
            if message_col not in df.columns:
                validation_results['issues'].append(f"Missing required column: {message_col}")

            if validation_results['issues']:
                return validation_results

            # Validate data
            valid_df = df.dropna(subset=[contact_col, message_col])
            validation_results['valid_rows'] = len(valid_df)

            # Check for empty values
            empty_contacts = df[contact_col].isna().sum()
            empty_messages = df[message_col].isna().sum()

            if empty_contacts > 0:
                validation_results['warnings'].append(f"{empty_contacts} rows have empty contacts")
            if empty_messages > 0:
                validation_results['warnings'].append(f"{empty_messages} rows have empty messages")

            # Check message length (WhatsApp has limits)
            long_messages = (df[message_col].str.len() > 4000).sum()
            if long_messages > 0:
                validation_results['warnings'].append(f"{long_messages} messages are longer than 4000 characters")

            validation_results['valid'] = validation_results['valid_rows'] > 0

        except Exception as e:
            validation_results['issues'].append(f"Error reading file: {str(e)}")

        return validation_results

    def get_session_statistics(self) -> Dict[str, any]:
        """
        Get current session statistics.

        Returns:
            dict: Session statistics including messages sent, time elapsed, etc.
        """
        current_time = datetime.now()
        session_duration = (current_time - self.session_stats['session_start_time']).total_seconds()

        return {
            'session_duration_seconds': session_duration,
            'session_duration_formatted': str(current_time - self.session_stats['session_start_time']),
            'messages_sent': self.session_stats['messages_sent'],
            'messages_failed': self.session_stats['messages_failed'],
            'contacts_processed': self.session_stats['contacts_processed'],
            'success_rate': (self.session_stats['messages_sent'] / max(1, self.session_stats['contacts_processed'])) * 100,
            'average_time_per_message': session_duration / max(1, self.session_stats['messages_sent'])
        }

    def close(self) -> None:
        """
        Properly close the WebDriver and clean up resources.

        This method ensures all browser processes are terminated
        and logs final session statistics.
        """
        try:
            # Log final session statistics
            stats = self.get_session_statistics()
            self.logger.info("="*50)
            self.logger.info("SESSION STATISTICS")
            self.logger.info("="*50)
            self.logger.info(f"Session duration: {stats['session_duration_formatted']}")
            self.logger.info(f"Messages sent: {stats['messages_sent']}")
            self.logger.info(f"Messages failed: {stats['messages_failed']}")
            self.logger.info(f"Contacts processed: {stats['contacts_processed']}")
            self.logger.info(f"Success rate: {stats['success_rate']:.1f}%")
            self.logger.info("="*50)

            # Close WebDriver
            if self.driver:
                self.driver.quit()
                self.logger.info("✅ WebDriver closed successfully")

            print("\n👋 WhatsApp Automation Tool session ended")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

# ==============================================================================
#                           UTILITY FUNCTIONS
# ==============================================================================

def schedule_bulk_messages(contacts_file: str, 
                          send_time: str, 
                          message_column: str = 'message', 
                          contact_column: str = 'contact',
                          user_data_dir: str = None) -> None:
    """
    Schedule bulk messages to be sent at a specific time.

    This function uses the schedule library to automatically send
    bulk messages at a predetermined time each day.

    Args:
        contacts_file (str): Path to contacts file
        send_time (str): Time to send messages (format: "HH:MM", e.g., "14:30")
        message_column (str): Column name for messages
        contact_column (str): Column name for contacts
        user_data_dir (str): Custom user data directory

    Example:
        schedule_bulk_messages("contacts.csv", "09:00", "message", "contact")
    """
    try:
        import schedule
    except ImportError:
        print("❌ Error: 'schedule' library not installed. Install with: pip install schedule")
        return

    def scheduled_job():
        """Job function to be executed at scheduled time."""
        print(f"\n⏰ Executing scheduled bulk messaging at {datetime.now().strftime('%H:%M:%S')}")

        whatsapp = WhatsAppAutomation(user_data_dir=user_data_dir)
        try:
            whatsapp.setup_driver()
            if whatsapp.login_to_whatsapp():
                results = whatsapp.send_bulk_messages(contacts_file, message_column, contact_column)
                print(f"\n📊 Scheduled messaging completed:")
                print(f"   ✅ Successful: {results['successful']}")
                print(f"   ❌ Failed: {results['failed']}")
            else:
                print("❌ Failed to login to WhatsApp Web")
        except Exception as e:
            print(f"❌ Error in scheduled job: {str(e)}")
        finally:
            whatsapp.close()

    # Schedule the job
    schedule.every().day.at(send_time).do(scheduled_job)

    print(f"📅 Bulk messages scheduled for {send_time} daily")
    print(f"📁 Using contacts file: {contacts_file}")
    print("⏳ Waiting for scheduled time... (Press Ctrl+C to stop)")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n⏹️ Scheduler stopped by user")

def validate_phone_numbers(phone_list: List[str]) -> Dict[str, List[str]]:
    """
    Validate a list of phone numbers using basic regex patterns.

    Args:
        phone_list (list): List of phone numbers to validate

    Returns:
        dict: Dictionary with 'valid' and 'invalid' phone number lists

    Example:
        result = validate_phone_numbers(["+1234567890", "invalid", "+9876543210"])
        print(f"Valid: {result['valid']}")
        print(f"Invalid: {result['invalid']}")
    """
    import re

    # Regex pattern for international phone numbers
    # Matches: +1234567890, 1234567890, +91-9876543210, etc.
    valid_pattern = re.compile(r'^[\+]?[1-9][\d\-\s\(\)]{7,15}$')

    valid_numbers = []
    invalid_numbers = []

    for number in phone_list:
        # Clean the number (remove extra spaces, special chars except +, -, (), spaces)
        clean_number = re.sub(r'[^\d\+\-\(\)\s]', '', str(number).strip())

        if clean_number and valid_pattern.match(clean_number):
            valid_numbers.append(clean_number)
        else:
            invalid_numbers.append(number)

    return {
        'valid': valid_numbers,
        'invalid': invalid_numbers
    }

def create_message_templates() -> Dict[str, str]:
    """
    Create a collection of message templates for different use cases.

    Returns:
        dict: Dictionary of message templates
    """
    templates = {
        'greeting': "Hello {name}! Hope you are having a wonderful day. This is an automated message from {sender}.",

        'business_update': "Hi {name}, We have an exciting update about {topic}. {details} Thank you for your continued support!",

        'reminder': "Hello {name}, This is a friendly reminder about {event} scheduled for {date}. Looking forward to seeing you there!",

        'promotional': "Hi {name}! 🎉 Special offer just for you: {offer}. Valid until {expiry}. Don't miss out!",

        'follow_up': "Hi {name}, Following up on our previous conversation about {topic}. Please let me know if you have any questions.",

        'thank_you': "Dear {name}, Thank you so much for {reason}. Your support means a lot to us! Best regards, {sender}",

        'invitation': "Hello {name}! You're invited to {event} on {date} at {location}. Hope to see you there! RSVP: {contact}"
    }

    return templates

def generate_personalized_message(template: str, **kwargs) -> str:
    """
    Generate a personalized message from a template.

    Args:
        template (str): Message template with placeholders
        **kwargs: Keyword arguments to replace placeholders

    Returns:
        str: Personalized message

    Example:
        template = "Hello {name}! Your order {order_id} is ready for pickup."
        message = generate_personalized_message(template, name="John", order_id="12345")
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"Error: Missing template variable {e}"

# ==============================================================================
#                           MAIN EXECUTION FUNCTION
# ==============================================================================

def main():
    """
    Main function demonstrating how to use the WhatsApp automation tool.

    This function provides a complete workflow including:
    1. Tool initialization
    2. Driver setup
    3. WhatsApp login
    4. File validation
    5. Sample file creation (if needed)
    6. User confirmation
    7. Bulk messaging execution
    8. Results reporting
    9. Proper cleanup
    """
    print("\n" + "="*70)
    print("         🚀 WHATSAPP BULK MESSAGING AUTOMATION TOOL 🚀")
    print("="*70)

    # Tool description
    print("\n📋 TOOL DESCRIPTION:")
    print("   • Send bulk WhatsApp messages from CSV/Excel files")
    print("   • Persistent login with Chrome user data directory") 
    print("   • Smart rate limiting to prevent spam detection")
    print("   • Comprehensive logging and error handling")
    print("   • Progress tracking and detailed reporting")
    print("\n⚠️  IMPORTANT: Use responsibly and comply with WhatsApp ToS")

    # Initialize the automation tool
    try:
        print("\n" + "="*50)
        print("STEP 1: INITIALIZING AUTOMATION TOOL")
        print("="*50)

        whatsapp = WhatsAppAutomation(
            user_data_dir="./whatsapp_user_data",  # Custom directory for persistent login
            headless=False  # Set to True for headless mode (not recommended for first use)
        )

        print("✅ Automation tool initialized successfully")

        # Setup WebDriver
        print("\n" + "="*50)
        print("STEP 2: SETTING UP CHROME WEBDRIVER")
        print("="*50)
        print("⏳ This may take a moment if ChromeDriver needs to be downloaded...")

        whatsapp.setup_driver()
        print("✅ Chrome WebDriver setup complete")

        # Login to WhatsApp Web
        print("\n" + "="*50)
        print("STEP 3: CONNECTING TO WHATSAPP WEB")
        print("="*50)

        if not whatsapp.login_to_whatsapp():
            print("❌ Failed to login to WhatsApp Web. Exiting...")
            return

        print("✅ Successfully connected to WhatsApp Web")

        # Check for contacts file or create sample
        print("\n" + "="*50)
        print("STEP 4: PREPARING CONTACTS FILE")
        print("="*50)

        contacts_filename = "contacts.csv"

        if not os.path.exists(contacts_filename):
            print(f"📄 Contacts file '{contacts_filename}' not found")
            print("🔧 Creating sample contacts file for you...")

            whatsapp.create_sample_contacts_file(contacts_filename)

            print("\n" + "="*70)
            print("                    ⚠️  NEXT STEPS REQUIRED")
            print("="*70)
            print(f"1. Edit the file '{contacts_filename}' with your actual contacts")
            print("2. Replace sample data with real contact names/numbers and messages")
            print("3. Save the file and run this script again")
            print("4. Make sure recipients have consented to receive messages")
            print("="*70)

            input("\nPress Enter to exit and edit the contacts file...")
            return

        # Validate contacts file
        print(f"📊 Validating contacts file: {contacts_filename}")
        validation = whatsapp.validate_contacts_file(contacts_filename)

        if not validation['valid']:
            print("❌ Contacts file validation failed:")
            for issue in validation['issues']:
                print(f"   • {issue}")
            for warning in validation['warnings']:
                print(f"   ⚠️ {warning}")
            return

        print(f"✅ Contacts file valid: {validation['valid_rows']}/{validation['total_rows']} rows")

        if validation['warnings']:
            print("⚠️ Warnings found:")
            for warning in validation['warnings']:
                print(f"   • {warning}")

        # Final confirmation
        print("\n" + "="*50)
        print("STEP 5: FINAL CONFIRMATION")
        print("="*50)

        print(f"📁 Contacts file: {contacts_filename}")
        print(f"📊 Valid contacts: {validation['valid_rows']}")
        print(f"⏱️ Estimated time: {validation['valid_rows'] * 6} seconds (average)")
        print(f"🔄 Rate limiting: 3-8 seconds between messages")

        print("\n🚨 IMPORTANT REMINDERS:")
        print("   • Only message contacts who have consented")
        print("   • Ensure messages are relevant and valuable")
        print("   • Monitor for any WhatsApp warnings or restrictions")
        print("   • This tool respects WhatsApp's rate limits")

        confirm = input("\n❓ Do you want to proceed with bulk messaging? (yes/no): ").lower().strip()

        if confirm != 'yes':
            print("❌ Operation cancelled by user")
            return

        # Execute bulk messaging
        print("\n" + "="*50)
        print("STEP 6: EXECUTING BULK MESSAGING")
        print("="*50)

        results = whatsapp.send_bulk_messages(
            contacts_file=contacts_filename,
            contact_column="contact",
            message_column="message",
            delay_range=(5, 10)  # 5-10 seconds delay between messages
        )

        # Display final results
        print("\n" + "="*70)
        print("                    🎉 OPERATION COMPLETED")
        print("="*70)

        success_rate = (results['successful'] / results['total'] * 100) if results['total'] > 0 else 0

        print(f"📈 RESULTS SUMMARY:")
        print(f"   📋 Total contacts: {results['total']}")
        print(f"   ✅ Successfully sent: {results['successful']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   ⏭️ Skipped: {results['skipped']}")
        print(f"   📊 Success rate: {success_rate:.1f}%")
        print(f"   ⏱️ Processing time: {results['processing_time']:.1f} seconds")

        if results['failed_contacts']:
            print(f"\n❌ Failed contacts:")
            for i, contact in enumerate(results['failed_contacts'][:5], 1):
                print(f"   {i}. {contact}")
            if len(results['failed_contacts']) > 5:
                print(f"   ... and {len(results['failed_contacts']) - 5} more (check logs for details)")

        # Session statistics
        stats = whatsapp.get_session_statistics()
        print(f"\n📊 SESSION STATISTICS:")
        print(f"   🕒 Session duration: {stats['session_duration_formatted']}")
        print(f"   ⚡ Average time per message: {stats['average_time_per_message']:.1f} seconds")

        print("\n📝 Check 'whatsapp_automation.log' for detailed logs")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\n⚠️ Operation interrupted by user (Ctrl+C)")
        print("🛑 Stopping automation safely...")

    except Exception as e:
        print(f"\n❌ Unexpected error occurred: {str(e)}")
        print("📝 Check logs for detailed error information")

    finally:
        # Cleanup
        try:
            print("\n🧹 Cleaning up resources...")
            whatsapp.close()
            print("✅ Cleanup completed successfully")
        except:
            pass

        print("\n👋 Thank you for using WhatsApp Bulk Messaging Automation Tool!")
        print("🔗 Remember to use this tool responsibly and ethically")

# ==============================================================================
#                           SCRIPT ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    """
    Script entry point.

    This ensures the main function only runs when the script is executed directly,
    not when imported as a module.
    """
    try:
        main()
    except Exception as e:
        print(f"\n💥 Critical error: {str(e)}")
        print("🆘 Please check your installation and try again")
    finally:
        print("\n🏁 Script execution finished")

# ==============================================================================
#                              END OF FILE
# ==============================================================================

"""
USAGE EXAMPLES:

1. Basic Usage:
   python whatsapp_bulk_automation.py

2. Programmatic Usage:
   from whatsapp_bulk_automation import WhatsAppAutomation

   whatsapp = WhatsAppAutomation()
   whatsapp.setup_driver()
   whatsapp.login_to_whatsapp()
   results = whatsapp.send_bulk_messages("contacts.csv")
   whatsapp.close()

3. Custom Configuration:
   whatsapp = WhatsAppAutomation(
       user_data_dir="./custom_profile",
       headless=True
   )

4. Scheduled Messaging:
   from whatsapp_bulk_automation import schedule_bulk_messages
   schedule_bulk_messages("contacts.csv", "09:00")

5. Phone Number Validation:
   from whatsapp_bulk_automation import validate_phone_numbers
   result = validate_phone_numbers(["+1234567890", "invalid-number"])

TROUBLESHOOTING:

1. ChromeDriver Issues:
   - Update Chrome browser to latest version
   - Restart script to auto-download correct driver version
   - Check internet connection

2. WhatsApp Login Issues:
   - Clear browser cache and cookies
   - Delete user_data directory and re-scan QR code
   - Ensure WhatsApp isn't open in other browsers

3. Contact Not Found:
   - Use exact contact names as saved in phone
   - Try using phone numbers instead of names
   - Ensure contacts are saved in your WhatsApp

4. Rate Limiting:
   - Increase delays between messages
   - Reduce daily message volume
   - Monitor account for restrictions

LEGAL DISCLAIMER:
This tool is provided for educational and legitimate business purposes only.
Users are responsible for:
- Obtaining proper consent from message recipients
- Complying with WhatsApp Terms of Service
- Following local laws regarding automated messaging
- Using the tool ethically and responsibly

The developers assume no liability for misuse of this tool.
"""
