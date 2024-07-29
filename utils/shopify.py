import os
import shopify
import requests
import json

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
        raise Exception(f"Shopify API Error for {url}. Error: {response.text}")


def get_order_data(shipwire_order_id: str, shipwire_order_piece_id: str):
    shipwire_order = shipwire.get_order(shipwire_order_id)
    shipwire_order_pieces = shipwire.get_order_pieces(
        shipwire_order_id, shipwire_order_piece_id)

    if not shipwire_order or not shipwire_order_pieces:
        raise ValueError(
            f"Invalid data. shipwire_order: {shipwire_order}, shipwire_order_pieces: {shipwire_order_pieces}")

    # Get Shopify Order
    order_number = shipwire_order['orderNo'].split(".")[0]
    shopify_order = shopify.Order.find_first(name=order_number, status="any")

    if not shopify_order:
        raise Exception("Shopify Order not found. ")

    # Get Shopify Line Items
    line_items_by_fulfillment_order = []
    update_fulfillment = None

    fulfillment_orders = get_fulfillment_orders(shopify_order.id)

    for fulfillment_order in fulfillment_orders:
        fulfillment_order_line_items = []

        for shipwire_order_piece in shipwire_order_pieces:
            sku = shipwire_order_piece['resource']['sku']
            quantity = shipwire_order_piece['resource']['quantity']

            # Base Product
            for fulfillment_order_line_item in fulfillment_order['line_items']:
                variant = shopify.Variant.find(
                    fulfillment_order_line_item['variant_id'])

                # Check if bundle
                kit_skus = shipwire.get_kits(sku=variant.sku)
                if sku in kit_skus:
                    # Get fulfillment
                    fulfillments = get_fulfillments(fulfillment_order['id'])
                    print(fulfillments)
                    if len(fulfillments) > 0:
                        # Todo - get exact fulfillment id in case there are several bundle items in an order.
                        fulfillment_id = fulfillments[0].get('id')
                        if fulfillment_id:
                            update_fulfillment = {
                                'id': fulfillment_id,
                                'urls': fulfillments[0].get('tracking_urls', [])
                            }

                if fulfillment_order['status'] != "closed":
                    if variant.sku == sku or (sku in kit_skus and not update_fulfillment):
                        fulfillment_order_line_items.append({
                            'id': fulfillment_order_line_item['id'],
                            'quantity': quantity
                        })

        if len(fulfillment_order_line_items) > 0:
            line_items_by_fulfillment_order.append({
                "fulfillment_order_id": fulfillment_order['id'],
                "fulfillment_order_line_items": fulfillment_order_line_items
            })

    print(line_items_by_fulfillment_order)
    print(update_fulfillment)

    return shopify_order, line_items_by_fulfillment_order, update_fulfillment


def get_fulfillment_orders(order_id: str) -> list:
    fulfillment_orders_data = request_api(
        "GET", f"/orders/{order_id}/fulfillment_orders.json")

    return [
        fo for fo in fulfillment_orders_data.get('fulfillment_orders', [])
        if fo['status'] in ["open", "in_progress", "closed"]
    ]


def get_fulfillments(fulfillment_order_id: str) -> list:
    fulfillments_data = request_api(
        "GET", f"/fulfillment_orders/{fulfillment_order_id}/fulfillments.json")

    return [
        f for f in fulfillments_data.get('fulfillments', [])
        if f['status'] in ["success"]
    ]


def update_order_tracking(tracking_data: dict, test=None) -> bool:
    with shopify.Session.temp(SHOPIFY_API_BASE_URL, SHOPIFY_API_VERSION, SHOPIFY_ACCESS_TOKEN):
        # Get Shipwire Order ID and Order Price ID from Webhook Data
        shipwire_order_id = tracking_data['orderId']
        shipwire_order_piece_id = tracking_data['pieceId']

        if not shipwire_order_id or not shipwire_order_piece_id:
            raise Exception(
                f"Invalid data. shipwire_order_id: {shipwire_order_id}, shipwire_order_piece_id: {shipwire_order_piece_id}")

        # Get Shopify Order Data and Line Items
        shopify_order, line_items_by_fulfillment_order, update_fulfillment = get_order_data(
            shipwire_order_id, shipwire_order_piece_id)
        if not shopify_order:
            raise Exception("Shopify Order not found.")

        # Dev mode
        if test and test != shopify_order.email:
            return

        # Fulfill Line Items
        if len(line_items_by_fulfillment_order) > 0:
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
            print(json.dumps(fulfillment_attributes, indent=4))

            response = request_api(
                method="POST",
                url="/fulfillments.json",
                payload=fulfillment_attributes
            )

            if response and response.get('fulfillment', {}).get('status') == "success":
                print(
                    f"Tracking information for Order {shopify_order.id} updated successfully.")
            else:
                raise Exception(
                    f"Failed to update tracking information to Shopify. Response: {response}")

        else:
            print("No items left to fulfill, or item is bundle.")

        # Update tracking for bundle
        if update_fulfillment:
            print(update_fulfillment)

            mutation = """
                mutation fulfillmentTrackingInfoUpdateV2($fulfillmentId: ID!, $trackingInfoInput: FulfillmentTrackingInput!, $notifyCustomer: Boolean) {
                    fulfillmentTrackingInfoUpdateV2(fulfillmentId: $fulfillmentId, trackingInfoInput: $trackingInfoInput, notifyCustomer: $notifyCustomer) {
                        fulfillment {
                            id
                            status
                            trackingInfo {
                                company
                                number
                                url
                            }
                        }
                        userErrors {
                            field
                            message
                        }
                    }
                }
            """

            tracking_urls = update_fulfillment.get('urls', [])
            tracking_urls.append(tracking_data['url'])
            variables = {
                "fulfillmentId": f"gid://shopify/Fulfillment/{update_fulfillment['id']}",
                "notifyCustomer": False,
                "trackingInfoInput": {
                    "urls": tracking_urls
                }
            }

            print(tracking_urls)

            shopifyGraphQL = shopify.GraphQL()
            graphql_response = shopifyGraphQL.execute(mutation, variables=variables)
            response = json.loads(graphql_response)

            if response and response.get('fulfillment', {}).get('status') == "success":
                print(
                    f"Tracking information for Order {shopify_order.id} updated successfully.")
            else:
                raise Exception(
                    f"Failed to update tracking information to Shopify. Response: {response}")
