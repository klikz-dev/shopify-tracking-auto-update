import os
import shopify

import shipwire

SHOPIFY_API_BASE_URL = os.environ.get('SHOPIFY_API_BASE_URL')
SHOPIFY_API_VERSION = os.environ.get('SHOPIFY_API_VERSION')
SHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN')


def update_order_tracking(tracking_data):
    with shopify.Session.temp(SHOPIFY_API_BASE_URL, SHOPIFY_API_VERSION, SHOPIFY_ACCESS_TOKEN):

        shipwire_order_id = tracking_data['orderId']
        shipwire_order_piece_id = tracking_data['pieceId']

        if not shipwire_order_id or not shipwire_order_piece_id:
            print("Invalid data format.")
            return False

        shipwire_order = shipwire.get_order(shipwire_order_id)
        shipwire_order_pieces = shipwire.get_order_pieces(
            shipwire_order_id, shipwire_order_piece_id)

        if not shipwire_order or not shipwire_order_pieces:
            print("Invalid order or order piece data.")
            return False

        order_number = str(shipwire_order['orderNo']).split(".")[
            0].replace("#", "")
        shopify_order = shopify.Order.find(names=order_number)
        if not shopify_order:
            print(f"Order {order_number} not found.")
            return False

        shopify_line_items = []
        for piece in shipwire_order_pieces:
            try:
                sku = piece['resource']['sku']
                quantity = piece['resource']['quantity']
                shopify_line_items.append({
                    'sku': sku,
                    'quantity': quantity
                })
            except:
                continue

        fulfillment = shopify.Fulfillment({
            "order_id": shopify_order.id,
            "line_items": shopify_line_items,
            "tracking_company": tracking_data['carrier'],
            "tracking_number": tracking_data['tracking'],
            "tracking_url": tracking_data['url'],
            "notify_customer": False,
        })

        if fulfillment.save():
            print("Tracking information updated successfully.")
        else:
            print(fulfillment.errors.full_messages())
            print("Failed to update tracking information.")
