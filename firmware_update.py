from io import BytesIO
import os
from time import sleep, time
from tkinter import EXCEPTION
import requests
import spdlog as spd
import zipfile
import shutil
import urllib
from pathlib import Path

MAX_SIZE = 1024 * 1024 * 1
MAX_FILES = 0
version = ""
latest_version = ""
extract_path = os.path.join(os.getcwd(), 'saved')
if not os.path.isdir('ADDDI_LOGS'):
    os.mkdir('ADDDI_LOGS')
firmware_logger = spd.RotatingLogger("ADDDI Jetson Nano", "ADDDI_LOGS/ADDDI_Jetson_Nano_FirmWare_Update.log", 1, MAX_SIZE, MAX_FILES)
SERVER_IP = "http://132.226.227.252/"
DOWNLOAD_PATH = "versions/"

def download_extract_zip(url):
    method_name = "download_extract_zip"

    # check firmware version is latest
    if version != latest_version:

        firmware_logger.info("[" + method_name + "] Try to download version: '" + latest_version + "' code")
        firmware_logger.flush()
        # Downloading the file by sending the request to the URL
        try :
            download_url = url + latest_version + '/code.zip'
            req = requests.get(download_url)
            firmware_logger.info("[" + method_name + "] Downloading Completed")
            firmware_logger.flush()
            makedir('saved')
        except Exception as e:
            firmware_logger.error("[" + method_name + "] Failed to download new firmware") 
            firmware_logger.flush()   
        else: # Success downloading
            file_size = req.headers["Content-Length"]
            file_type = req.headers["Content-Type"]
            
            # Try to download what latest firmware is bigger than 150MB(check firmware validation)
            if file_type == "application/zip" and int(file_size) > 1024 * 1024 * 150  :
                # extracting the zip file contents
                zip = zipfile.ZipFile(BytesIO(req.content))
                zip.extractall(extract_path)
                firmware_logger.info("[" + method_name + "] Extract zip file")
                firmware_logger.flush()
                
                # get files from extrated folder
                extract_files = os.listdir(extract_path)
                firmware_logger.info("[" + method_name + "] Get file list")
                firmware_logger.flush()
                
                # replace files from extracted file to original folder
                for extract_file_name in extract_files :
                    if not 'MAC' in extract_file_name:
                        os.replace(os.path.join(extract_path, extract_file_name), os.path.join(os.getcwd(), extract_file_name))
                        firmware_logger.info("[" + method_name + "] Replace old code(" + extract_file_name + ") with new code")

                shutil.rmtree(os.getcwd() + '/saved', ignore_errors=True)
                firmware_logger.info("[" + method_name + "] Delete 'saved' folder")
                firmware_logger.flush()
                shutil.rmtree(os.getcwd() + '/code.zip', ignore_errors=True)
                firmware_logger.info("[" + method_name + "] Delete zip file")
                firmware_logger.flush()
                
                write_latest_version(latest_version)
                firmware_logger.info("[" + method_name + "] Start to Reboot!!!")
                firmware_logger.flush()
                os.system("sudo shutdown -r now")
            else :
                firmware_logger.error("[" + method_name + "] File is not 'zip' type or file is smaller than 100MB") 
                firmware_logger.flush()
    else :
        firmware_logger.info('[{}] Current version is latest version'.format(method_name))
        firmware_logger.info('[{}] Starting Main APP'.format(method_name))
        firmware_logger.flush()
        os.system('python3 /home/addd-jetson/FastMOT/app.py')

def makedir(directory):
    method_name = "makedir"
    if not os.path.exists(directory):
        os.makedirs(directory)
        firmware_logger.info("[" + method_name + "] Make 'saved' folder")
        firmware_logger.flush()


def is_firmware_latest():
    method_name = "is_firmware_latest"
    latest_version = "1.1.0"
    # get latest version from Server API
    # latest_version = API()
    try :
        firmware_logger.info("[" + method_name + "] Get versions list")    
        firmware_logger.flush()
        return latest_version
    except Exception as e:
        firmware_logger.error("[" + method_name + "] Failed to get version list, " +  str(e))
        firmware_logger.flush()


def is_network_connected():
    method_name = "is_network_connected"
    # check internet
    test_url = 'http://google.com'
    firmware_logger.info("[" + method_name + "] connecting to <{}> for internet connection test".format(test_url))
    firmware_logger.flush()
    try :
        urllib.request.urlopen(test_url)
        firmware_logger.info("[" + method_name + "] internet connected")
        firmware_logger.flush()
        return True
    except :
        firmware_logger.error("[" + method_name + "] internet not connected")
        firmware_logger.flush()
        return False
    
def check_network_connection(rebooting = False):
    # check network and reboot
    firmware_logger.info('[check_network_connection] checking network conneced')
    firmware_logger.flush()
    check_repeat_count = 0
    max_check_repeat_count = 10
    sleep_second = 30
    while(True) :
        # repeat about max_check_repeat_count
        if check_repeat_count ==  ( max_check_repeat_count - 1 ) :
            firmware_logger.error('[check_network_connection] internet is not connected... rebooting')
            firmware_logger.flush()
            if rebooting :
                os.system('sudo reboot')
            else :
                break
        connected = is_network_connected()
        if connected :
            return True
        sleep(sleep_second)
        check_repeat_count += 1
    return False
    
def get_version():
    method_name = 'get_version'
    
    if not os.path.exists('version.txt'):
        firmware_logger.info("[" + method_name + "] Make version.txt")
        firmware_logger.flush()
        f = open(os.getcwd() + "/version.txt", "w")
        f.write('0.0.0')
        f.close()
    
    f = open(os.getcwd() + "/version.txt", "r")
    firmware_logger.info("[" + method_name + "] Read version.txt")
    firmware_logger.flush()
    lines = f.readlines()
    for line in lines:
        line = line.strip()  # last line 
    f.close()
    return line


def write_latest_version(latest_version):
    method_name = "write_latest_version"
    firmware_logger.info("[" + method_name + "] Rewrite version.txt")
    firmware_logger.flush()
    shutil.rmtree(os.getcwd() + '/version.txt', ignore_errors=True)
    f = open(os.getcwd() + "/version.txt", "w")
    f.write(latest_version) 
    f.close()


if __name__ == "__main__":
    # check network is alived
    if check_network_connection() :
        version = get_version()
        update_url = SERVER_IP + DOWNLOAD_PATH
        latest_version = is_firmware_latest()
        download_extract_zip(update_url)
