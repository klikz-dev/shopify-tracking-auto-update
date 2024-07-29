import os
import json
import requests

SHIPWIRE_API_BASE_URL = os.environ.get('SHIPWIRE_API_BASE_URL')
SHIPWIRE_API_KEY = os.environ.get('SHIPWIRE_API_KEY')


def get_order(shipwire_order_id):
    response = requests.get(
        f"{SHIPWIRE_API_BASE_URL}/orders/{shipwire_order_id}",
        headers={
            'Authorization': f"ShipwireKey {SHIPWIRE_API_KEY}"
        }
    )

    data = json.loads(response.text)
    return data['resource']


def get_order_piece(shipwire_order_id, piece_id):
    response = requests.get(
        f"{SHIPWIRE_API_BASE_URL}/orders/{shipwire_order_id}/pieces",
        headers={
            'Authorization': f"ShipwireKey {SHIPWIRE_API_KEY}"
        }
    )

    data = json.loads(response.text)

    for item in data['resource']['items']:
        if item['resource']['id'] == piece_id:
            return item['resource']['contents']['resource']['items'][0]['resource']


def get_order_trackings(shipwire_order_id):
    response = requests.get(
        f"{SHIPWIRE_API_BASE_URL}/orders/{shipwire_order_id}/trackings",
        headers={
            'Authorization': f"ShipwireKey {SHIPWIRE_API_KEY}"
        }
    )

    data = json.loads(response.text)
    return data['resource']['items']


def get_kits(sku):
    response = requests.get(
        f"{SHIPWIRE_API_BASE_URL}/products?classification=virtualKit&sku={sku}",
        headers={
            'Authorization': f"ShipwireKey {SHIPWIRE_API_KEY}"
        }
    )

    product_data = json.loads(response.text)

    for product in product_data['resource']['items']:
        if product['resource']['sku'] == sku:
            product_id = product['resource']['id']

            response = requests.get(
                f"""{SHIPWIRE_API_BASE_URL}/products/virtualKits/{
                    product_id}/content?classification=virtualKit""",
                headers={
                    'Authorization': f"ShipwireKey {SHIPWIRE_API_KEY}"
                }
            )

            kits_data = json.loads(response.text)

            kit_skus = []
            for kit in kits_data['resource']['items']:
                kit_skus.append(kit['resource']['sku'])

            return kit_skus

    return []
