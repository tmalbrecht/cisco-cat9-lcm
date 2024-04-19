[![python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org)
![Repo Size](https://img.shields.io/github/repo-size/Sulstice/global-chem)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

# Life Cycle Management for Cisco Catalyst 9000 switches

This code will retrieve life cycle management infromation from all types of Cisco Catalyst 9000 series switches. It will create an excell sheet and send it to a desired email address. Logging is generated. See logging section below.


Following information will be included in the excell sheet:

  * Software version
  * Hardware model
  * Uptime
  * Serial number
  * MAC
  * Is smart licensing enabled?
  * Licensing transport method
  * Licensing last ack
  * Is trust code installed?

## Code logic

This code uses Netmiko for all switch communication and sends the following commands. 

  * show version
  * show license all

The Genie library is used for parsing the output from the commands above to stuctured data. The openpyxl library is used to generatle the xlsx file. The smtplib library is used for sending the email. 

The code can deal with chassis and stacked switches. If a switch is a stack it will retrieve mac and serial number from everry switch in the stack and store it in the excell sheet.

## Getting Started

### Prerequisites

The things you need before installing the software:

* Linux environment: The code uses the pyATS Genie library for parsing. Genie is only supported in Linux.
* Python 3.11.0rc1 (code is developed in this version, didn't test it in other versions but anything older should be fine)
* Check the requirements.txt file for all the libraries you need, best practice is to use a seperate venv.
  
### Installation

Move to a directory where you want to store the repository and type the following command:

```
$ git clone https://github.com/tmalbrecht/cisco-cat9-lcm.git
```

Install all necessary libraries (make sure to use a venv):

```
$ pip3 install -r requirements.txt
```

Create devices.yaml file and add switch details, example file is included in this GitHub repository.

Create .env file and fill in all your details like credentials and smtp info, example file is included in this GitHub repository.

Create the following directories:
  * /logs/
  * /logs/session/
  * /logs/detailed/
  * /reports/
    
Code will fail if they are not present.

## Logging

When running the code, logs are created and stored in the /logs/ directory. This directory needs to be inside your code directory or adjust in code if desired. 

The following logs are created:
  * Session logs : The excact output from every switch connection is stored into the directory /logs/session/
  * Detailed log : Will show if retrieving information from every switch was succesfull or not. If not it will show why it possibly failed. This logging is stored into the directory /logs/detailed/.

This detailed log file is icluded in the email if the script failed to retrieve information from one or more switches. 

The detailed logs name is a timestamp that shows when the script was executed. The session logs name is the device name + a timestamp that shows when connection was made with the switch.

## Usage

Navigate into the project directory and execute main.py:

```
$ python main.py
```

If you have not filled in any credentials for switch login inside the .env file it will prompt you for the credentials. For password getpass() is used to keep it hidden.

Check your email. The generated xlsx file will also be stored in the /reports/ directory inside the code directory. Check logs if there are any issues.




