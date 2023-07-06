import requests
import datetime
import base64
import img2pdf
from fpdf import FPDF
import os
from dotenv import load_dotenv

load_dotenv()
tokens = eval(os.getenv("WB_TOKENS"))


def get_new_orders_to_pack_wb(token):
    host = "https://suppliers-api.wildberries.ru/api/v3/orders/new"
    headers = {"Authorization": token}
    req = requests.get(url=host, headers=headers)
    print(req)
    load = req.json()
    orders_id = {}
    for i in load['orders']:
        orders_id[i["id"]] = i["article"]
    return orders_id


def make_new_shipment(token):
    shipment_name = datetime.datetime.now().strftime("%Y.%m.%dT%H:%M:%S")
    host = "https://suppliers-api.wildberries.ru/api/v3/supplies"
    headers = {"Authorization": token}
    params = {"name": shipment_name}
    req = requests.post(url=host, headers=headers, json=params)
    print(req)
    load = req.json().get("id")
    return load


def add_order_to_shipment(token, shipment_id, order_id):
    host = f"https://suppliers-api.wildberries.ru/api/v3/supplies/{shipment_id}/orders/{order_id}"
    headers = {"Authorization": token}
    params = {"supply": shipment_id, "order": order_id}
    req = requests.patch(url=host, headers=headers, params=params)
    print(req)


def get_stikers_for_orders_in_shipment(shop, token, orders_list):
    host = "https://suppliers-api.wildberries.ru/api/v3/orders/stickers"
    headers = {"Authorization": token}
    params = {"type": "png", "width": 58, "height": 40}
    json = {"orders": orders_list}
    req = requests.post(url=host, headers=headers, params=params, json=json)
    print(req)
    load = req.json().get("stickers")
    stikers_img = []
    stikers_info = {}
    for i in load:
        stikers_img.append(base64.urlsafe_b64decode(i.get("file")))
        stikers_info[i.get("orderId")] = f"{i.get('partA')} {i.get('partB')}"
    with open(f"{datetime.datetime.now().strftime('%Y.%m.%d')} Wildberries {shop} Stickers.pdf", "wb") as f:
        f.write(img2pdf.convert(stikers_img))
    return stikers_info


def set_shipment_to_supply(shipment, token):
    host = f"https://suppliers-api.wildberries.ru/api/v3/supplies/{shipment}/deliver"
    headers = {"Authorization": token}
    # params = {"supply": shipment_id, "order": order_id}
    req = requests.patch(url=host, headers=headers)
    print(req)


def get_stiker_for_shipment(shop, token, shipment):
    host = f"https://suppliers-api.wildberries.ru/api/v3/supplies/{shipment}/barcode"
    headers = {"Authorization": token}
    params = {"type": "png"}
    req = requests.get(url=host, headers=headers, params=params)
    print(req)
    load = req.json()
    print(load)
    stiker_img = base64.urlsafe_b64decode(load.get("file"))
    with open(f"{datetime.datetime.now().strftime('%Y.%m.%d')} Wildberries {shop} shipment_list.pdf", "wb") as f:
        f.write(img2pdf.convert(stiker_img))


def get_assembly_sheet(shop, order_list):
    order_list = [["Order number", "Order label", "SKU"]]+order_list

    class PDF(FPDF):
        def header(self):
            # Arial bold 15
            self.set_font('Arial', 'B', 15)
            # Title
            self.cell(60, 5, f'Wildberries - {shop}')
            # self.cell(30, 10, str(shop))
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'R')
            self.ln()
            # Date
            self.cell(30, 10, f"{datetime.datetime.now().strftime('%d-%m-%Y')}")
            # Line break
            self.ln(10)
    print(order_list)
    pdf = PDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font("Times", size=12)
    for order_number, order_label, sku in order_list:
        pdf.cell(30, 10, str(order_number), 1)
        pdf.cell(50, 10, str(order_label), 1)
        pdf.cell(110, 10, str(sku), 1)
        pdf.ln(10)
    pdf.output(f"{datetime.datetime.now().strftime('%Y.%m.%d')} Wildberries {shop} assemble_list.pdf")


def main():
    for shop, token in tokens:
        orders = get_new_orders_to_pack_wb(token)
        order_tabs = []
        print(orders)
        if orders:
            shipment_id = make_new_shipment(token)
            print(shipment_id)
            for order, article in orders.items():
                add_order_to_shipment(token, shipment_id, order)
            stikers_info = get_stikers_for_orders_in_shipment(shop, token, list(orders.keys()))
            for order, article in orders.items():
                order_tabs.append([order, stikers_info[order], article])
            get_assembly_sheet(shop, order_tabs)
            set_shipment_to_supply(shipment_id, token)
            get_stiker_for_shipment(shop, token, shipment_id)


if __name__ == "__main__":
    main()
