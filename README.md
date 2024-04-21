[![python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org)
![Repo Size](https://img.shields.io/github/repo-size/Sulstice/global-chem)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# Life Cycle Management for Cisco Catalyst 9000 switches

This script is designed to extract lifecycle management information from all types of Cisco Catalyst 9000 series switches. It will generate an Excel spreadsheet with the collected data and send it to a specified email address if desired.

The Excel sheet will include the following information:

 * Software Version
 * Hardware Model
 * Uptime
 * Serial Number
 * MAC Address
 * Smart Licensing Status
 * Licensing Transport Method
 * Last Licensing Acknowledgment
 * Trust Code Installation Status

## Code logic

This script utilizes Netmiko for communication (ssh) with all switches, executing the following commands:

  * show version
  * show license all

It employs the Genie library to parse the output from these commands into structured data. The openpyxl library is used to generate the Excel file, while smtplib manages the email sending process.

The code is equipped to handle both chassis and stacked switches. In the case of stacked switches, it retrieves the MAC and serial numbers from each switch in the stack and records this information in the Excel sheet.

## Getting Started

### Prerequisites

Before installing the software, ensure you have the following prerequisites:

 * Linux Environment: The script utilizes the pyATS Genie library for parsing, which is only supported on Linux platforms.
 * Python Version: The code is developed in Python 3.11.0rc1. Although it has not been tested on other versions, newer versions should generally be compatible.
 * Library Dependencies: Refer to the requirements.txt file for all necessary libraries. It is recommended to use a separate virtual environment (venv) for installation to avoid conflicts with existing packages.
  
### Installation

Go to the directory where you intend to save the repository and execute the following command:

```
git clone https://github.com/tmalbrecht/cisco-cat9-lcm.git
```

Move into the directory and setup a Python virtual environment:

```
cd cisco-cat9-lcm
python3 -m venv venv 
source venv/bin/activate
```

Install all required libraries:

```
pip3 install -r requirements.txt
```

Create the devices.yml file and edit it:
```
touch devices.yml
nano devices.yml
```

Enter your switch details into the file as shown below; you can copy and paste them directly into nano:

```
---
cisco_1:
  device_type: cisco_xe
  host: 192.168.178.45

cisco_2:
  device_type: cisco_xe
  host: 192.168.178.46

cisco_3:
  device_type: cisco_xe
  host: 192.168.178.47

cisco:
  - cisco_1
  - cisco_2
  - cisco_3
```
Close the file by typing ctrl + x, type 'y' and after press enter.

Create the .env file and edit it:
```
touch devices.yml
nano devices.yml
```

Enter your credentials and email details into the file as shown below; you can copy and paste them directly into nano:
```
# Credentials used for login into the switches by ssh.
# Leave blank if you don't want to store them here for security reasons.
# The script will prompt you when excuting it
PASSWORD_SSH =""
USERNAME_SSH =""

# Details needed for sending the email.
# Leave password blank if you don't want to store them here for security reasons.
# The script will prompt you when excuting it.
RECEIVER_EMAIL = "email@example.nl"
SENDER_EMAIL = "email@example.nl"
PASSWORD_EMAIL = ""
SMTP_SERVER = "smtp.your_server.com"
SMTP_PORT = "587"
```
Close the file by typing ctrl + x, type 'y' and after press enter.

## Security 

Please ensure that your credentials and email details are not stored in a script within a directory where others have read permissions. If the SSH login credentials for the switch and email password are not specified in the .env file, you will be prompted to enter them when executing the script. The getpass() function is used to securely handle your passwords, ensuring it remains hidden at all times.

## Logging

When the code is executed, it generates logs that are stored in the /logs/ directory. If this directory does not already exist, it will be automatically created within the script directory.

The following logs are created:
  * Session Logs: These logs capture the exact output from each switch connection and are stored in the /logs/session/ directory.
  * Detailed Log: This log details whether the retrieval of information from each switch was successful. If unsuccessful, it provides possible reasons for the failure. These logs are stored in the /logs/detailed/ directory.

If the script fails to retrieve information from one or more switches, the detailed log file is included in the email notification. 

The filename for the detailed logs includes a timestamp indicating when the script was executed. Session logs are named using the device name followed by a timestamp that marks the exact moment the connection was made with the switch.

## Usage

Navigate into the project directory and execute main.py:

```
python main.py
```

If you haven't entered any credentials for switch login in the .env file, you will be prompted to provide them. The getpass() function is used to ensure that your passwords remain hidden.

After you will get prompted with the question if you want to send an email with the report or not.

If you haven't entered an email password in the .env file, you will be prompted to provide it. The getpass() function is used to ensure that your passwords remain hidden.

See example output below:


Please check your email for the generated Excel file, which is also saved in the /reports/ directory within the code directory. Refer to the logs for any issues that may have occurred.




