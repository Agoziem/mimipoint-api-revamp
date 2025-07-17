from typing import Optional
from app.core.config import settings
import requests

class Paystack:
    PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
    base_url = "https://api.paystack.co"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    def verify_payment(self, ref, *args, **kwargs):
        url = f"{self.base_url}/transaction/verify/{ref}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            return data['status'], data['data']
        data = response.json()
        return data['status'], data['message']

    def get_balance(self):
        url = f"{self.base_url}/balance"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return True, response.json()["data"]
        return False, response.json()

    def create_transfer_recipient(self, name: str, account_number: str, bank_code: str, currency: str = "NGN"):
        url = f"{self.base_url}/transferrecipient"
        payload = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": currency
        }
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200 or response.status_code == 201:
            return True, response.json()["data"]
        return False, response.json()

    def initiate_transfer(self, recipient_code: str, amount: int, reason: str = ""):
        url = f"{self.base_url}/transfer"
        payload = {
            "source": "balance",
            "amount": amount,
            "recipient": recipient_code,
            "reason": reason
        }
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200 or response.status_code == 201:
            return True, response.json()["data"]
        return False, response.json()

    def finalize_transfer(self, transfer_code: str, otp: str):
        url = f"{self.base_url}/transfer/finalize_transfer"
        payload = {
            "transfer_code": transfer_code,
            "otp": otp
        }
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200:
            return True, response.json()["data"]
        return False, response.json()

    def get_payout_history(self, status: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None):
        url = f"{self.base_url}/settlement"
        params = {}
        if status:
            params["status"] = status
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return True, response.json()["data"]
        return False, response.json()

    def create_customer(self, email: str, first_name: str, last_name: str, phone: str):
        url = f"{self.base_url}/customer"
        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone
        }
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200 or response.status_code == 201:
            return True, response.json()["data"]
        return False, response.json()

    def create_virtual_account(self, customer_code: str, preferred_bank: str = "test-bank"):
        url = f"{self.base_url}/dedicated_account"
        payload = {
            "customer": customer_code,
            "preferred_bank": preferred_bank
        }
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200 or response.status_code == 201:
            return True, response.json()["data"]
        return False, response.json()
