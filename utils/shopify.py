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


def get_order(order_number):
    with shopify.Session.temp(SHOPIFY_API_BASE_URL, SHOPIFY_API_VERSION, SHOPIFY_ACCESS_TOKEN):
        shopify_order = shopify.Order.find_first(
            name=order_number, status="any")
        if not shopify_order:
            raise Exception(f"Shopify Order {order_number} not found. ")

        return shopify_order


def get_variant(variant_id):
    with shopify.Session.temp(SHOPIFY_API_BASE_URL, SHOPIFY_API_VERSION, SHOPIFY_ACCESS_TOKEN):
        shopify_variant = shopify.Variant.find(variant_id)
        if not shopify_variant:
            raise Exception(f"Shopify Variant {variant_id} not found. ")

        return shopify_variant


def create_fulfillment(mutation, variables):
    with shopify.Session.temp(SHOPIFY_API_BASE_URL, SHOPIFY_API_VERSION, SHOPIFY_ACCESS_TOKEN):
        shopifyGraphQL = shopify.GraphQL()
        graphql_response = shopifyGraphQL.execute(
            mutation, variables=variables)
        response = json.loads(graphql_response)

        return response


def get_fulfillment_orders(order_id: str) -> list:
    fulfillment_orders_data = request_api(
        "GET", f"/orders/{order_id}/fulfillment_orders.json")

    return [
        fo for fo in fulfillment_orders_data.get('fulfillment_orders', [])
        if fo['status'] in ["open", "in_progress"]
    ]
