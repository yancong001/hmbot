import asyncio
import base64
import hashlib
import hmac
import logging
import sys
import unittest
from os.path import join, realpath
from typing import Any, Awaitable, Dict
from unittest.mock import MagicMock

import aiohttp
import ujson

import conf
from hummingbot.connector.exchange.bitget import bitget_constants as CONSTANTS
from hummingbot.connector.exchange.bitget.bitget_auth import BitgetAuth
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSJSONRequest
from hummingbot.logger.struct_logger import METRICS_LOG_LEVEL

sys.path.insert(0, realpath(join(__file__, "../../../../../")))
logging.basicConfig(level=METRICS_LOG_LEVEL)


class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ev_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()
        cls.api_key = ""
        cls.secret_key = ""
        cls.passphrase = ""
        cls._time_synchronizer_mock = MagicMock()
        cls._time_synchronizer_mock.time.return_value = 1640001112.223
        cls.auth = BitgetAuth(cls.api_key, cls.secret_key, cls.passphrase, cls._time_synchronizer_mock)

    def test_add_auth_to_rest_request(self):
        params = {"one": "1"}
        request = RESTRequest(
            method=RESTMethod.GET,
            url="https://test.url",
            throttler_limit_id="/api/endpoint",
            params=params,
            is_auth_required=True,
            headers={},
        )

        self.async_run_with_timeout(self.auth.rest_authenticate(request))

        raw_signature = (request.headers.get("ACCESS-TIMESTAMP")
                         + request.method.value
                         + request.throttler_limit_id + "?one=1")
        expected_signature = base64.b64encode(
            hmac.new(self.secret_key.encode("utf-8"), raw_signature.encode("utf-8"), hashlib.sha256).digest()
        ).decode().strip()

        params = request.params

        self.assertEqual(1, len(params))
        self.assertEqual("1", params.get("one"))
        self.assertEqual(
            self._time_synchronizer_mock.time(),
            int(request.headers.get("ACCESS-TIMESTAMP")) * 1e-3)
        self.assertEqual(self.api_key, request.headers.get("ACCESS-KEY"))
        self.assertEqual(expected_signature, request.headers.get("ACCESS-SIGN"))
        self.assertEqual(expected_signature, request.headers.get("ACCESS-SIGN"))

    def async_run_with_timeout(self, coroutine: Awaitable, timeout: int = 1):
        ret = asyncio.get_event_loop().run_until_complete(asyncio.wait_for(coroutine, timeout))
        return ret

    def test_ws_auth_payload(self):
        payload = self.auth.get_ws_auth_payload()

        raw_signature = str(int(self._time_synchronizer_mock.time())) + "GET/user/verify"
        expected_signature = base64.b64encode(
            hmac.new(self.secret_key.encode("utf-8"), raw_signature.encode("utf-8"), hashlib.sha256).digest()
        ).decode().strip()

        self.assertEqual(1, len(payload))
        self.assertEqual(self.api_key, payload[0]["apiKey"])
        self.assertEqual(str(int(self._time_synchronizer_mock.time())), payload[0]["timestamp"])
        self.assertEqual(expected_signature, payload[0]["sign"])

    def test_no_auth_added_to_ws_request(self):
        payload = {"one": "1"}
        request = WSJSONRequest(payload=payload, is_auth_required=True)

        self.async_run_with_timeout(self.auth.ws_authenticate(request))

        self.assertEqual(payload, request.payload)


    # async def rest_auth_post(self) -> Dict[Any, Any]:
    #     endpoint = CONSTANTS.ORDER_CREATE_PATH_URL
    #     http_client = aiohttp.ClientSession()
    #     order_params = ujson.dumps({
    #         'currency_pair': 'ETH_BTC',
    #         'type': 'limit',
    #         'side': 'buy',
    #         'amount': '0.00000001',
    #         'price': '0.0000001',
    #     })
    #     headers = self.auth.get_headers("POST", f"{CONSTANTS.REST_URL_AUTH}/{endpoint}", order_params)
    #     http_status, response, request_errors = await rest_response_with_errors(
    #         http_client.request(
    #             method='POST', url=f"{CONSTANTS.REST_URL}/{endpoint}", headers=headers, data=order_params
    #         )
    #     )
    #     await http_client.close()
    #     return response
    #
    # async def ws_auth(self) -> Dict[Any, Any]:
    #     ws = GateIoWebsocket(api_factory=build_gate_io_api_factory(
    #         throttler=AsyncThrottler(CONSTANTS.RATE_LIMITS)),
    #         auth=self.auth)
    #     await ws.connect()
    #     await ws.subscribe(CONSTANTS.USER_BALANCE_ENDPOINT_NAME)
    #     async for response in ws.on_message():
    #         if ws.is_subscribed:
    #             return True
    #         return False


    # def test_rest_auth_post(self):
    #     result = self.ev_loop.run_until_complete(self.rest_auth_post())
    #     if "message" not in result.keys():
    #         print(f"Unexpected response for API call: {result}")
    #     assert "message" in result.keys()
    #     assert "Your order size 0.00000001 is too small" in result['message']
    #
    # def test_ws_auth(self):
    #     response = self.ev_loop.run_until_complete(self.ws_auth())
    #     assert response is True
