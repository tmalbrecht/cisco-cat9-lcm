from netmiko import ConnLogOnly
from datetime import datetime
from getpass import getpass
from dotenv import load_dotenv
import yaml
import logging
import os
from openpyxl import Workbook
from openpyxl import load_workbook
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


# Load yaml file with all network devices
def load_devices(device_file="devices.yml"):
    device_dict = {}
    with open(device_file) as f:
        device_dict = yaml.safe_load(f)
    return device_dict


# create file name for session logging with timestamp
def get_log_name(device_name):
    log_name = "logs/session/" + get_time() + "_" + device_name + ".log"
    return log_name


# Get the current local date/time and format the object to a string in a readable format
def get_time():
    time = datetime.now()
    time = time.strftime("%Y-%m-%d_%H:%M:%S")
    return time


# Creat an xlsx file for the report
def create_xlsx(filename):
    wb = Workbook()
    ws = wb.create_sheet(title="Software")
    header = ["Device", "Software"]
    ws.append(header)
    ws.auto_filter.ref = "A1:B1"
    ws = wb.create_sheet(title="Serial and Mac")
    ws = wb.create_sheet(title="License")
    if "Sheet" in wb.sheetnames:
        std = wb["Sheet"]
        wb.remove(std)
    wb.save(filename)
    logging.info("LCM report file created in xlsx file type.")


# Write output to report
def write_output_xlsx(filename, output, device_name):
    if output:
        version = output["version"]["version"]
    else:
        version = "unknown"
    row = [device_name, version]
    wb = load_workbook(filename)
    custom_sheet = wb["Software"]
    custom_sheet.append(row)
    wb.save(filename)
    logging.info("Output is processed and written to xlsx file.")


# Handle connection to network device, return boolean True when connection was succesfull and false if otherwhise
def connect_to_device(device, username, password, device_name, filename):
    device["username"] = username
    device["password"] = password
    device["session_log"] = get_log_name(device_name)
    ip = device["host"]
    logging.info(f"Starting connection to device: {device_name} ({ip})")
    net_connect = ConnLogOnly(**device)
    output = False
    if net_connect:
        output = net_connect.send_command("show version", use_genie=True)
        net_connect.disconnect()
        logging.info(f"Successfully closed connection to device: {device_name} ({ip})")
        if isinstance(output, str):
            logging.error(
                "Failed to get output from the given command. Possibly the command syntax is wrong or unknown in the Cisco Genie library.",
                exc_info=True,
            )
            output = False
            write_output_xlsx(filename, output, device_name)
            return False
        write_output_xlsx(filename, output, device_name)
        return True
    write_output_xlsx(filename, output, device_name)
    return False


# Prompt for username
def get_username():
    print("Username: ", end="")
    username = input()
    return username


def create_email_body(devices_no_connect):
    if devices_no_connect:
        email_body = (
            "Couldn't connect to the following device(s) to retrieve information: "
        )
        for device in devices_no_connect:
            email_body += f"\n  *{device}"
        email_body += "\nCheck logging for more details."
    else:
        email_body = "Connection to all devices was successfull."
    return email_body


# Send email with report as attachment
def send_email(filename, devices_no_connect):
    sender_email = os.getenv("SENDER_EMAIL")
    password_email = os.getenv("PASSWORD_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    email_body = create_email_body(devices_no_connect)

    # Create email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "LCM Report Cisco Catalyst"
    message.attach(MIMEText(email_body, "plain"))

    # Attach file
    file_to_attach = filename
    part = MIMEBase("application", "octet-stream")
    with open(file_to_attach, "rb") as file:
        part.set_payload(file.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition", f'attachment; filename="{file_to_attach.split("/")[-1]}"'
    )
    message.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to TLS
            server.login(sender_email, password_email)
            server.sendmail(sender_email, receiver_email, message.as_string())
            logging.info("Email sent successfully with attachment")
    except Exception:
        logging.error("Failed to send email", exc_info=True)


if __name__ == "__main__":
    # Load environment variables, store username and password if present, otherwise prompt for input
    load_dotenv()
    username = (
        os.getenv("USERNAME_SSH") if os.getenv("USERNAME_SSH") else get_username()
    )
    password = os.getenv("PASSWORD_SSH") if os.getenv("PASSWORD_SSH") else getpass()

    # Enable detailed logging, put logging level on INFO if to much detail
    logging.basicConfig(
        filename=f"logs/detailed/{get_time()}.log",
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Set filename for the report and create it
    filename = "reports/LCM_REPORT_CISCO_CAT9_" + get_time() + ".xlsx"
    report = create_xlsx(filename)

    # load all devices in a dictionary variable
    devices_dict = load_devices()

    # store all cisco device hostnames in a list variable
    device_list = devices_dict["cisco"]

    # loop over all device names, and connect to every device, store device names of all connections that failed
    devices_no_connect = []
    for device_name in device_list:
        device = devices_dict[device_name]
        connect = connect_to_device(device, username, password, device_name, filename)
        if not connect:
            devices_no_connect.append(device_name)

    # send email with LCM report as attachment
    send_email(filename, devices_no_connect)
