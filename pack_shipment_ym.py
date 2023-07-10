import requests
import datetime
import time
from pypdf import PdfMerger
from fpdf import FPDF
import os
from dotenv import load_dotenv

load_dotenv()
campaign_id = eval(os.getenv("YM_CAMPAIGN_ID"))
api_key = eval(os.getenv("YM_API_KEY"))


def get_orders_to_shipment(shop, campaignId, warehouse_id):
    headers = {"Accept": "application/json",
               "Authorization": f"OAuth oauth_token = {api_key['OAUTH_TOKEN']}, "
                                f"oauth_client_id = {api_key['OAUTH_CLIENT_ID']}"}

    url = f"https://api.partner.market.yandex.ru/campaigns/{campaignId}"
    params = {"status": "PROCESSING",
              "supplierShipmentDateFrom": datetime.datetime.now().strftime('%d-%m-%Y'),
              "supplierShipmentDateTo": datetime.datetime.now().strftime('%d-%m-%Y')
              }
    r = requests.get(url=f"{url}/orders", headers=headers, params=params)
    load = r.json()
    pdfs = []
    assembly_sheet = []
    if load.get("orders"):
        for order in load.get("orders"):
            orderID = order.get("id")
            count = 0
            for item in order.get("items"):
                count += item.get("count")

            # send count of shipment boxes for each order
            json = {"boxes": [{} for _ in range(count)]}
            requests.put(url=f"{url}/orders/{orderID}/delivery/shipments/1/boxes", headers=headers, json=json)
            time.sleep(5)

            # get labels in .pdf for each order
            r = requests.get(url=f"{url}/orders/{orderID}/delivery/labels", headers=headers, params={"format":"A7"})
            filename = f"{datetime.datetime.now().strftime('%Y.%m.%d')} YM {shop} labels_{orderID}.pdf"
            pdfs.append(filename)
            with open(filename, "wb") as f:
                f.write(r.content)

            # set order status to "ready_to_ship"
            r = requests.put(url=f"{url}/orders/{orderID}/status",
                             headers=headers,
                             json={"order": {
                                 "status": "PROCESSING",
                                 "substatus": "READY_TO_SHIP"
                                    }
                                }
                             )
            order_info = r.json()
            print(order_info)
            for item in order_info.get("order").get("items"):
                assembly_sheet.append([orderID,
                                       order_info.get("order").get("substatus"),
                                       item.get("offerId"),
                                       item.get("count")])
        make_assembly_list(shop, assembly_sheet)

        # get act for shipment
        r = requests.get(url=f"{url}/shipments/reception-transfer-act", headers=headers, params={"warehouse_id": int(warehouse_id)})
        with open(f"{datetime.datetime.now().strftime('%Y.%m.%d')} YM {shop} Act.pdf", "wb") as f:
            f.write(r.content)

        # merging labels pdf`s file if they more then 1 and remove raw files

        merger = PdfMerger()
        for pdf in pdfs:
            merger.append(pdf)
        merger.write(f"{datetime.datetime.now().strftime('%Y.%m.%d')} YM {shop} labels.pdf")
        merger.close()
        for pdf in pdfs:
            os.remove(pdf)


def make_assembly_list(shop, assembly_sheet):
    assembly_sheet = [["Order number", "Order status", "SKU", "Quantity"]]+assembly_sheet

    class PDF(FPDF):
        def header(self):
            # Arial bold 15
            self.set_font('Arial', 'B', 15)
            # Title
            self.cell(60, 5, f'Yandex Market - {shop}')
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
        pdf.cell(30, 10, str(order_number), 1)
        pdf.cell(50, 10, str(order_status), 1)
        pdf.cell(90, 10, str(sku), 1)
        pdf.cell(20, 10, str(quantity), 1)
        pdf.ln()
    pdf.output(f"{datetime.datetime.now().strftime('%Y.%m.%d')} YM {shop} Assemble list.pdf")


def main():
    for shop, campaignId, warehouse_id in campaign_id:
        get_orders_to_shipment(shop, campaignId, warehouse_id)


if __name__ == "__main__":
    main()
