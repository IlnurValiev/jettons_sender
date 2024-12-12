from tonconnect.connector import AsyncConnector #folder
import asyncio #pip install asyncio
from argparse import Namespace
import aiohttp #pip install aiohttp
import qrcode #pip install qrcode[pil]


# Generating qr-code picture
async def generate_qr_code(url, output_file, max_data_size=500):

    data = url[:max_data_size]

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_file)


# Async rest requests
class Rest():

	async def __init__(self, response, text, json):
		self.response = response
		self.text = text
		self.json = json


	async def get(url: str, json: dict = None):

		response_status = None
		response_text = None
		response_json = None

		async with aiohttp.ClientSession() as session:
			response = await session.get(url=url, json=json)

			response_status = response.status

			try:
				response_text = await response.text(encoding='UTF-8')
				response_json = await response.json()
			except Exception as e:
				pass

		return Namespace(type='get', url=url, status=response_status, json=response_json)


# Creating connect bridge
async def TonConnect(url_path_to_json: str, provider: str, payload: str):

	connector = AsyncConnector(url_path_to_json)
	connect_url = await connector.connect(provider, payload)

	return connector, connect_url


async def main():

	api_endpoint = 'https://dev.tondex.tech'
	api_key = '45fdgWUfmawoe2-'


	connector, url = await TonConnect(f'https://nomore.eu.ngrok.io/grok/ton-connect.json', 'tonkeeper', 'unique_payload')
	#connector, url = await TonConnect(f'https://nomore.eu.ngrok.io/grok/ton-connect.json', 'tonhub', 'unique_payload')


	qr_code = await generate_qr_code(url, 'code.png')

	"""
		url - link to connect the user
		connector - builded object
		qr_code - qr code picture
	"""

	address = await connector.get_address() #(maybe save it)

	"""
		get_address() will wait for the user connect
	"""


	url = f'{api_endpoint}/get_jettonwallet_by_wallet'

	data = {
		'api_key': api_key,

		'address': str(address), #user address
		'jetton_master_address': 'EQB3b71N9iZvS0wjC7z1sMEE08mclkQvsJBMA8_dGiAQ7032' #ex. https://tonscan.org/address/EQB3b71N9iZvS0wjC7z1sMEE08mclkQvsJBMA8_dGiAQ7032
	}
	r = await Rest.get(url=url, json=data)
	jetton_wallet_address = r.json['jetton_wallet'] #(maybe save it)


	url = f'{api_endpoint}/get_jettonwallet_balance'

	data = {
		'api_key': api_key,

		'jetton_wallet_address': jetton_wallet_address #ex. https://tonscan.org/address/EQA4b6yY1mB1ZXKplcGA6B6pxnCzL14xHpZgdXkCn96bPqJJ
	}
	r = await Rest.get(url=url, json=data)
	print(r.json)


# asyncio.run(main())