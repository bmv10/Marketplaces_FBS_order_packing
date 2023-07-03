import requests
import datetime
import time
from fpdf import FPDF
import os
from dotenv import load_dotenv

load_dotenv()
tokens = eval(os.getenv("OZON_TOKENS"))

def get_orders_to_shipment(clientID, token, status):
    url = "https://api-seller.ozon.ru/v3/posting/fbs/unfulfilled/list"
    date_ship = datetime.datetime.now().strftime("%Y-%m-%d")
    headers = {"Client-Id": clientID, "Api-Key": token, "Content-Type": "application/json"}
    json = {"dir": "ASC",
            "filter": {
                "cutoff_from": f"{date_ship}T00:01:00Z",
                "cutoff_to": f"{date_ship}T23:59:00Z",
                "delivery_method_id": [],
                "provider_id": [],
                "status": status,
                "warehouse_id": []
            },
            "limit": 100,
            "offset": 0,
            "with": {
                "analytics_data": False,
                "barcodes": False,
                "financial_data": False,
                "translit": False
            }
            }
    r = requests.post(url, headers=headers, json=json)
    print(r)
    load = r.json()
    print(load)
    posting_numbers = []
    delivery_method = []
    assemble_list = []
    for i in load["result"]["postings"]:
        if i:
            if status == "awaiting_packaging":
                set_awaiting_deliver_for_order(i, clientID, token)
            else:
                assemble_list.append([i.get("posting_number"), i.get("status"), i.get("products")[0].get("offer_id"), i.get("products")[0].get("quantity")])
                posting_numbers.append(i.get("posting_number"))
                delivery_method.append(i.get("delivery_method").get("id"))
    print(posting_numbers, delivery_method)
    return posting_numbers, delivery_method, assemble_list


def set_awaiting_deliver_for_order(order, clientID, token):
    posting_number = order.get("posting_number")
    products = order.get("products")
    json = {"packages": [],
            "posting_number": posting_number,
            "with": {"additional_data": True}
            }
    for i in products:
        for j in range(i.get("quantity")):
            json["packages"].append({"products":
                [
                    {"exemplar_info":
                        [
                            {"gtd": "string",
                             "is_gtd_absent": True,
                             "mandatory_mark": "string"
                             }
                        ],
                        "product_id": i.get("sku"),
                        "quantity": 1
                    }
                ]
            }
            )
    url = "https://api-seller.ozon.ru/v3/posting/fbs/ship"
    headers = {"Client-Id": clientID, "Api-Key": token, "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=json)
    print(r)
    load = r.json()
    print(load)


def create_package_label(posting_numbers, clientID, token):
    url = "https://api-seller.ozon.ru/v1/posting/fbs/package-label/create"
    headers = {"Client-Id": clientID, "Api-Key": token, "Content-Type": "application/json"}
    json = {"posting_number": posting_numbers}
    r = requests.post(url, headers=headers, json=json)
    print(r)
    load = r.json()
    print(load)
    return load.get("result").get("task_id")


def get_package_label(taskID, shop, clientID, token):
    url = "https://api-seller.ozon.ru/v1/posting/fbs/package-label/get"
    headers = {"Client-Id": clientID, "Api-Key": token, "Content-Type": "application/json"}
    json = {"task_id": taskID}
    r = requests.post(url, headers=headers, json=json)
    print(r)
    load = r.json()
    if r.status_code == 200:
        while load.get("result").get("file_url") == "":
            time.sleep(60)
            r = requests.post(url, headers=headers, json=json)
            load = r.json()
    link = load.get("result").get("file_url")
    r = requests.get(link)
    with open(f'{datetime.datetime.now().strftime("%Y.%m.%d")} OZON {shop} Labels.pdf', 'wb') as f:
        f.write(r.content)


def create_act(delivery_method, clientID, token):
    url = "https://api-seller.ozon.ru/v2/posting/fbs/act/create"
    headers = {"Client-Id": clientID, "Api-Key": token, "Content-Type": "application/json"}
    json = {  # "containers_count": 1,
        "delivery_method_id": delivery_method,
        "departure_date": datetime.datetime.now().strftime("%Y-%m-%dT13:00:00.000Z")
    }
    r = requests.post(url, headers=headers, json=json)
    print(r)
    load = r.json()
    return load.get("result").get("id")


def get_package_act(taskID_act, shop, clientID, token):
    url = "https://api-seller.ozon.ru/v2/posting/fbs/digital/act/get-pdf"
    headers = {"Client-Id": clientID, "Api-Key": token, "Content-Type": "application/json"}
    json = {"id": taskID_act,
            "doc_type": "act_of_acceptance"}
    r = requests.post(url, headers=headers, json=json)
    print(r)
    load = r.content
    with open(f'{datetime.datetime.now().strftime("%Y.%m.%d")} OZON {shop} Act.pdf', 'wb') as f:
        f.write(load)

def make_assemble_list(shop, assembly_sheet):
    if assembly_sheet:
        assembly_sheet = [["Posting number", "Order status", "SKU", "Quantity"]]+assembly_sheet

        class PDF(FPDF):
            def header(self):
                # Arial bold 15
                self.set_font('Arial', 'B', 15)
                # Title
                self.cell(60, 5, f'OZON - {shop}')
                # self.cell(30, 10, str(shop))
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'R')
                self.ln()
                # Date
                self.cell(30, 10, f"{datetime.datetime.now().strftime('%d-%m-%Y')}")
                # Line break
                self.ln(10)

        pdf = PDF('P', 'mm', 'A4')
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_font("Arial", "", size=12)
        for order_number, order_status, sku, quantity in assembly_sheet:
            # for item in row:
            #     pdf.cell(45, 10, txt=str(item), border=1)
            pdf.cell(30, 10, str(order_number), 1)
            pdf.cell(50, 10, str(order_status), 1)
            pdf.cell(90, 10, str(sku), 1)
            pdf.cell(20, 10, str(quantity), 1)
            pdf.ln()
        pdf.output(f"{datetime.datetime.now().strftime('%Y.%m.%d')} Ozon {shop} assemble list.pdf")

def main():
    for shop, clientID, token in tokens:
        get_orders_to_shipment(clientID, token, "awaiting_packaging")
        posting_numbers, delivery_method, assemble_list = get_orders_to_shipment(clientID, token, "awaiting_deliver")
        if posting_numbers:
            task_id_labels = create_package_label(posting_numbers, clientID, token)
            for delivery_method_id in set(delivery_method):
                task_id_act = create_act(delivery_method_id, clientID, token)
                time.sleep(120)
                get_package_act(task_id_act, shop, clientID, token)
            get_package_label(task_id_labels, shop, clientID, token)
            print(shop, assemble_list)
            make_assemble_list(shop, assemble_list)


if __name__ == "__main__":
    main()
