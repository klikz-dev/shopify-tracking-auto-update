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
    try:
        resource = data.get('resource')
    except:
        resource = None

    return resource


def get_order_pieces(shipwire_order_id, shipwire_order_piece_id):
    response = requests.get(
        f"{SHIPWIRE_API_BASE_URL}/orders/{shipwire_order_id}/pieces/{shipwire_order_piece_id}",
        headers={
            'Authorization': f"ShipwireKey {SHIPWIRE_API_KEY}"
        }
    )

    data = json.loads(response.text)
    try:
        resource = data.get('resource').get('items')[
            0]['resource']['contents']['resource']['items']
    except:
        resource = None

    return resource
