import os
import json
import requests

RECHARGE_API_URL = os.environ.get('RECHARGE_API_URL', 'default_secret')
RECHARGE_API_KEY = os.environ.get('RECHARGE_API_KEY', 'default_secret')


def check_customer(email):

    customersRes = requests.request(
        "GET",
        f"{RECHARGE_API_URL}/customers?email={email}",
        headers={
            'X-Recharge-Access-Token': RECHARGE_API_KEY
        },
    )
    customersData = json.loads(customersRes.text)

    if len(customersData.get('customers', [])) > 0:
        return True
    else:
        return False


def create_customer(customer):

    customerRes = requests.request(
        "POST",
        f"{RECHARGE_API_URL}/customers",
        headers={
            'X-Recharge-Access-Token': RECHARGE_API_KEY
        },
        json=customer,
    )
    customerData = json.loads(customerRes.text)

    if customerRes.status_code == 200:
        customerId = customerData['customer']['id']
        return customerId
    else:
        print(customerRes.text)
        return None


def create_address(address):

    addressRes = requests.request(
        "POST",
        f"{RECHARGE_API_URL}/addresses",
        headers={
            'X-Recharge-Access-Token': RECHARGE_API_KEY
        },
        json=address,
    )
    addressData = json.loads(addressRes.text)

    if addressRes.status_code == 201:
        addressId = addressData['address']['id']
        return addressId
    else:
        print(addressRes.text)
        return None
