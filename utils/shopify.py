import os
import shopify
import requests

from . import shipwire

SHOPIFY_API_BASE_URL = os.getenv('SHOPIFY_API_BASE_URL')
SHOPIFY_API_VERSION = os.getenv('SHOPIFY_API_VERSION')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')


def request_api(method: str, url: str, payload: dict = None, params: dict = None) -> dict:
    headers = {'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN}
    if method not in ["GET", "DELETE"]:
        headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })

    response = requests.request(
        method,
        f"{SHOPIFY_API_BASE_URL}/{SHOPIFY_API_VERSION}{url}",
        params=params,
        headers=headers,
        json=payload
    )

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Shopify API Error for {url}. Error: {response.text}")
        return None


def get_order_data(shipwire_order_id: str, shipwire_order_piece_id: str):
    shipwire_order = shipwire.get_order(shipwire_order_id)
    shipwire_order_pieces = shipwire.get_order_pieces(
        shipwire_order_id, shipwire_order_piece_id)

    if not shipwire_order or not shipwire_order_pieces:
        print("Invalid order or order piece data.")
        return False

    order_number = shipwire_order['orderNo'].split(".")[0]
    shopify_order = shopify.Order.find_first(name=order_number, status="any")

    return shopify_order, shipwire_order_pieces


def get_fulfillment_orders(order_id: str) -> list:
    fulfillment_orders_data = request_api(
        "GET", f"/orders/{order_id}/fulfillment_orders.json")

    return [
        fo for fo in fulfillment_orders_data.get('fulfillment_orders', [])
        if fo['status'] in ["open", "in_progress"]
    ]


def update_order_tracking(tracking_data: dict) -> bool:
    with shopify.Session.temp(SHOPIFY_API_BASE_URL, SHOPIFY_API_VERSION, SHOPIFY_ACCESS_TOKEN):
        shipwire_order_id = tracking_data['orderId']
        shipwire_order_piece_id = tracking_data['pieceId']

        if not shipwire_order_id or not shipwire_order_piece_id:
            print("Invalid data format.")
            return False

        order, line_items = get_order_data(
            shipwire_order_id, shipwire_order_piece_id)
        if not order:
            return False

        fulfillment_orders = get_fulfillment_orders(order.id)

        line_items_by_fulfillment_order = [
            {
                "fulfillment_order_id": fo['id'],
                "fulfillment_order_line_items": [
                    {
                        'id': fl_item['id'],
                        'quantity': line_item['resource']['quantity']
                    }
                    for line_item in line_items
                    for variant in [shopify.Variant.find_first(sku=line_item['resource']['sku'])]
                    for fl_item in fo['line_items']
                    if variant.id == fl_item['variant_id']
                ]
            }
            for fo in fulfillment_orders
        ]

        fulfillment_attributes = {
            "fulfillment": {
                "line_items_by_fulfillment_order": line_items_by_fulfillment_order,
                "tracking_info": {
                    "company": tracking_data['carrier'],
                    "number": tracking_data['tracking'],
                    "url": tracking_data['url'],
                },
                "notify_customer": False,
            }
        }

        response = request_api(
            method="POST",
            url="/fulfillments.json",
            payload=fulfillment_attributes
        )

        if response and response.get('fulfillment', {}).get('status') == "success":
            print("Tracking information updated successfully.")
            return True
        else:
            print(response)
            print("Failed to update tracking information.")
            return False
