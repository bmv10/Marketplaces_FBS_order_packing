import smtplib
from dotenv import load_dotenv
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import yadisk
import datetime

load_dotenv()
mail_login = os.getenv("YA_MAIL_LOGIN")
mail_pass = os.getenv("YA_MAIL_PASS")
address_to = eval(os.getenv("ADDRESS_TO"))
address_from = os.getenv("ADDRESS_FROM")
address_for_reply = os.getenv("ADDRESS_REPLY_TO")
yadisk_token = os.getenv("YADISK_TOKEN")


def send_mail(file_list):
    if type(file_list) != list:
        print(f"Mail function: Type of filelist is not list, but {type(file_list)}")
        return None
    if not file_list:
        print("Mail function: There is no one file to send")
        return None
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Отгрузка {' '.join(file_list[0].split(' ')[0:2])}"
    msg['From'] = address_from
    msg['To'] = " ,".join(address_to)
    msg['Reply-To'] = address_for_reply
    msg['Return-Path'] = address_for_reply

    for file in file_list:
        if not os.path.exists(file):
            print(f"File '{file}' not found!")
            return None
        basename = os.path.basename(file)
        filesize = os.path.getsize(file)
        part_file = MIMEBase('application', 'octet-stream; name="{}"'.format(basename))
        part_file.set_payload(open(file, "rb").read())
        part_file.add_header('Content-Description', basename)
        part_file.add_header('Content-Disposition', 'attachment; filename="{}"; size={}'.format(basename, filesize))
        encoders.encode_base64(part_file)
        msg.attach(part_file)

    mail = smtplib.SMTP_SSL(host="smtp.yandex.ru", port=465)
    mail.login(mail_login, mail_pass)
    mail.sendmail(address_from, address_to, msg.as_string())
    mail.quit()
    print(f"Mail function: Letter wih docs for {msg['Subject']} was sent successfully.")


def send_yadisk(file_list=None):
    if type(file_list) == list:
        if file_list:
            y = yadisk.YaDisk(token=yadisk_token)
            print("Cheking YaDisk token:", y.check_token())
            disk_info = y.get_disk_info()
            print("Free space", round((disk_info.total_space-disk_info.used_space)/1048576, 2), "Mb")
            if not y.is_dir(folder_ := "/1. Shipment_documents"):
                print(f"Folder '{folder_}' not exist. Creating..")
                y.mkdir(folder_)
            if not y.is_dir(month_ := f"{folder_}/{datetime.datetime.now().strftime('%Y.%m')}"):
                print(f"Folder '{month_}' not exist. Creating..")
                y.mkdir(month_)
            for file in file_list:
                result = y.upload(file, f"{month_}/{file}")
                print(f"Uploaded file: {result.path}")
        else:
            print("YaDisk function: There is no one file to send")
    else:
        print(f"Type of filelist is not list, but {type(file_list)}")
