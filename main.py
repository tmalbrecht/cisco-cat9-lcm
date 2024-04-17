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
    ws = wb.create_sheet(title="General")
    header = ["Device","Software","Uptime"]
    ws.append(header)
    ws.auto_filter.ref = "A1:C1"
    ws = wb.create_sheet(title="Serial and Mac")
    header = ["Device","Mac"]
    ws.append(header)
    ws.auto_filter.ref = "A1:B1"
    ws = wb.create_sheet(title="License")
    if "Sheet" in wb.sheetnames:
        std = wb["Sheet"]
        wb.remove(std)
    wb.save(filename)
    logging.info("LCM report file created in xlsx file type.")


# Write output to report
def write_output_xlsx(filename, output_list, device_name):
    version = "unknown"
    uptime = "unknown"
    mac_address = "unknown"
    for output in output_list:
        if output:
            if "version" in output:
                version = output["version"]["version"]
                uptime = output["version"]["uptime"]
            elif "switch" in output:
                mac_address = output["switch"]["mac_address"]
    row_general = [device_name, version, uptime]
    row_sr_mac = [device_name, mac_address]
    wb = load_workbook(filename)
    custom_sheet = wb["General"]
    custom_sheet.append(row_general)
    custom_sheet = wb["Serial and Mac"]
    custom_sheet.append(row_sr_mac)
    wb.save(filename)
    logging.info("Output is processed and written to xlsx file.")

def send_command(net_connect,command):
    output = net_connect.send_command(command, use_genie=True)
    if isinstance(output, str):
        logging.error(
            f"Failed to get output from the command: <{command}>. Possibly the command syntax is wrong or unknown in the Cisco Genie library.",
            exc_info=True,
        )
        output =  False
    return output


# Handle connection to network device, return boolean True when connection was succesfull and false if otherwhise
def connect_to_device(device, username, password, device_name, filename):
    device["username"] = username
    device["password"] = password
    device["session_log"] = get_log_name(device_name)
    ip = device["host"]
    logging.info("*" * 60)
    logging.info(f"Starting connection to device: {device_name} ({ip})")
    logging.info("*" * 60)
    net_connect = ConnLogOnly(**device)
    output_list = []
    cmd_list = ["show version","show switch"]
    cmd_ok = True
    if net_connect:
        for cmd in cmd_list:
            output = send_command(net_connect,cmd)
            output_list.append(output)
            if not output:
                cmd_ok = False
        write_output_xlsx(filename, output_list, device_name)
        net_connect.disconnect()
        logging.info(f"Successfully closed connection to device: {device_name} ({ip})")
        if not cmd_ok:
            return False
        return True
    write_output_xlsx(filename, output_list, device_name)
    return False


# Prompt for username
def get_username():
    print("Username: ", end="")
    username = input()
    return username


def create_email_body(devices_no_connect):
    if devices_no_connect:
        email_body = (
            "Couldn't connect or retrieve desired information from the following device(s): "
        )
        for device in devices_no_connect:
            email_body += f"\n  *{device}"
        email_body += "\nCheck logging for more details."
    else:
        email_body = (
            "Connecting and retrieving information from all devices was successfull."
        )
    return email_body


# Send email with report as attachment
def send_email(filename, devices_no_connect, filename_logs):
    sender_email = os.getenv("SENDER_EMAIL")
    password_email = os.getenv("PASSWORD_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    email_body = create_email_body(devices_no_connect)
    logging.info(email_body)

    # Create email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "LCM Report Cisco Catalyst"
    message.attach(MIMEText(email_body, "plain"))
    

    # Attach file
    filenames = [filename]
    if devices_no_connect:
        filenames.append(filename_logs)
    for file_to_attach in filenames:
        part = MIMEBase("application", "octet-stream")
        try:
            with open(file_to_attach, "rb") as file:
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                "Content-Disposition",
                f'attachment; filename="{file_to_attach.split("/")[-1]}"',
            )
            message.attach(part)
            logging.info(f"Successfully added attachment {file_to_attach} to email")
        except Exception:
            logging.error(f"Failed to attach {file_to_attach} to email", exc_info=True)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to TLS
            server.login(sender_email, password_email)
            server.sendmail(sender_email, receiver_email, message.as_string())
            logging.info("Email sent successfully with attachment")
    except Exception:
        logging.error("Failed to send email", exc_info=True)

if __name__ == "__main__":
    start_time = datetime.now()
    # Load environment variables, store username and password if present, otherwise prompt for input
    load_dotenv()
    username = (
        os.getenv("USERNAME_SSH") if os.getenv("USERNAME_SSH") else get_username()
    )
    password = os.getenv("PASSWORD_SSH") if os.getenv("PASSWORD_SSH") else getpass()

    # Enable logging, put logging level on DEBUG if you want more detail
    filename_logs = f"logs/detailed/{get_time()}.log"
    logging.basicConfig(
        filename=filename_logs,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Set filename for the report and create it
    filename = "reports/LCM_REPORT_CISCO_CAT9_" + get_time() + ".xlsx"
    report = create_xlsx(filename)

    # Load all devices in a dictionary variable
    devices_dict = load_devices()

    # Store all cisco device hostnames in a list variable
    device_list = devices_dict["cisco"]

    # Loop over all device names, and connect to every device, store device names of all connections that failed
    devices_no_connect = []
    for device_name in device_list:
        device = devices_dict[device_name]
        connect = connect_to_device(device, username, password, device_name, filename)
        if not connect:
            devices_no_connect.append(device_name)

    # Send email with LCM report as attachment
    send_email(filename, devices_no_connect, filename_logs)

    # Add total runtime script to logging
    end_time = datetime.now()
    logging.info(f"\n\nScript execution time: {end_time - start_time}\n\n")

