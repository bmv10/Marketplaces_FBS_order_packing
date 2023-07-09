from pack_shipment_wb import main as main_wb
from pack_shipment_ym import main as main_ym
from pack_shipment_ozon import main as main_ozon


def main():
    main_wb()
    main_ym()
    main_ozon()


if __name__ == "__main__":
    main()
