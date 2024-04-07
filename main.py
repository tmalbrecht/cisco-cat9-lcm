from netmiko import ConnectHandler
from datetime import datetime
from getpass import getpass
from dotenv import load_dotenv
import yaml
import logging
import os


# load yaml file with all network devices
def load_devices(device_file="devices.yml"):
    device_dict = {}
    with open(device_file) as f:
        device_dict = yaml.safe_load(f)
    return device_dict


# create file name for session logging with timestamp
def get_log_name(device_name):
    log_name = "logs/session_logs/" + get_time() + "_" + device_name + ".log"
    return log_name


# get the current local date/time and format the object to a string in a readable format
def get_time():
    time = datetime.now()
    time = time.strftime("%Y-%m-%d_%H_%M_%S")
    return time


# write output to a file
def write_output(filename, output, device_name):
    version = output["version"]["version"]
    with open(filename, "a") as file:
        file.write("\n\n")
        file.write("*" * 200)
        file.write(f"\nOutput device: {device_name}\n")
        file.write("*" * 200)
        file.write("\n\n")
        file.write(f"Software version: {version}")


# handle connection to network device
def connect_to_device(device, username, password, device_name, filename):
    device["username"] = username
    device["password"] = password
    device["session_log"] = get_log_name(device_name)
    net_connect = ConnectHandler(**device)
    print(net_connect.find_prompt())
    output = net_connect.send_command("show version", use_genie=True)
    write_output(filename, output, device_name)
    net_connect.disconnect()


# prompt for username
def get_username():
    print("Username: ", end="")
    username = input()
    return username


if __name__ == "__main__":
    # Load environment variables, store username and password if present, otherwise prompt for input
    load_dotenv()
    username = os.getenv("USERNAME") if os.getenv("PASSWORD") else get_username()
    password = os.getenv("PASSWORD") if os.getenv("PASSWORD") else getpass()

    # set filename for the txt file with all output show commands, inlcude timestamp to make it unique and traceable
    filename = "output/output_" + get_time()

    # Enable detailed logging for Netmiko
    logging.basicConfig(filename=f"logs/detailed/{get_time()}", level=logging.DEBUG)
    logger = logging.getLogger("netmiko")

    # load all devices in a dictionary variable
    devices_dict = load_devices()

    # store all cisco device hostnames in a list variable
    device_list = devices_dict["cisco"]

    # loop over all device names, store the device details and connect to the device
    for device_name in device_list:
        device = devices_dict[device_name]
        connect_to_device(device, username, password, device_name, filename)
