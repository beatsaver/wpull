# encoding=utf-8

import copy
import unittest

from wpull.errors import ProtocolError
from wpull.http.request import Request, Response


class TestRequest(unittest.TestCase):
    def test_request(self):
        request = Request('http://example.com/robots.txt')
        request.prepare_for_send()
        self.assertEqual(
            (b'GET /robots.txt HTTP/1.1\r\n'
             b'Host: example.com\r\n'
             b'\r\n'),
            request.to_bytes()
        )

    def test_request_parse(self):
        request = Request()
        request.parse(b'GET /robots.txt HTTP/1.1\r\n')
        request.parse(b'Host: example.com\r\n')
        request.parse(b'\r\n')

        self.assertEqual('http://example.com/robots.txt', request.url)
        self.assertEqual('example.com', request.fields['host'])

        request = Request()
        request.parse(b'GET https://example.com/robots.txt HTTP/1.1\r\n')
        request.parse(b'Host: example.com\r\n')
        request.parse(b'\r\n')

        self.assertEqual('https://example.com/robots.txt', request.url)
        self.assertEqual('example.com', request.fields['host'])

    def test_response(self):
        response = Response(200, 'OK')
        response.fields['Cake'] = 'dolphin'

        self.assertEqual(
            (b'HTTP/1.1 200 OK\r\n'
             b'Cake: dolphin\r\n'
             b'\r\n'),
            response.to_bytes()
        )

    def test_response_parse(self):
        response = Response()
        response.parse(b'HTTP/1.0 200 OK\r\n')
        response.parse(b'Cake: dolphin\r\n')
        response.parse(b'\r\n')

        self.assertEqual(200, response.status_code)
        self.assertEqual('OK', response.reason)
        self.assertEqual('dolphin', response.fields['Cake'])

    def test_response_empty_reason_line(self):
        response = Response()
        response.parse(b'HTTP/1.0 200\r\n')
        response.parse(b'Cake: dolphin\r\n')
        response.parse(b'\r\n')

        self.assertEqual(200, response.status_code)
        self.assertEqual('', response.reason)
        self.assertEqual('dolphin', response.fields['Cake'])

    def test_response_status_codes(self):
        response = Response()
        response.parse(b'HTTP/1.0 0\r\n')
        response.parse(b'\r\n')

        self.assertEqual(0, response.status_code)

        response = Response()
        response.parse(b'HTTP/1.0 999\r\n')
        response.parse(b'\r\n')

        self.assertEqual(999, response.status_code)

        response = Response(0, '')
        self.assertEqual(0, response.status_code)

    def test_request_port(self):
        request = Request('https://example.com:4567/robots.txt')
        request.prepare_for_send()
        self.assertEqual(
            (b'GET /robots.txt HTTP/1.1\r\n'
             b'Host: example.com:4567\r\n'
             b'\r\n'),
            request.to_bytes()
        )

    def test_parse_status_line(self):
        version, code, msg = Response.parse_status_line(b'HTTP/1.0 200 OK')
        self.assertEqual('HTTP/1.0', version)
        self.assertEqual(200, code)
        self.assertEqual('OK', msg)

        version, code, msg = Response.parse_status_line(
            b'HTTP/1.0 404 Not Found')
        self.assertEqual('HTTP/1.0', version)
        self.assertEqual(404, code)
        self.assertEqual('Not Found', msg)

        version, code, msg = Response.parse_status_line(b'HTTP/1.1  200   OK')
        self.assertEqual('HTTP/1.1', version)
        self.assertEqual(200, code)
        self.assertEqual('OK', msg)

        version, code, msg = Response.parse_status_line(b'HTTP/1.1  200')
        self.assertEqual('HTTP/1.1', version)
        self.assertEqual(200, code)
        self.assertEqual('', msg)

        version, code, msg = Response.parse_status_line(b'HTTP/1.1  200  ')
        self.assertEqual('HTTP/1.1', version)
        self.assertEqual(200, code)
        self.assertEqual('', msg)

        version, code, msg = Response.parse_status_line(
            'HTTP/1.1 200 ððð'.encode('latin-1'))
        self.assertEqual('HTTP/1.1', version)
        self.assertEqual(200, code)
        self.assertEqual('ððð', msg)

        self.assertRaises(
            ProtocolError,
            Response.parse_status_line, b'HTTP/1.0'
        )
        self.assertRaises(
            ProtocolError,
            Response.parse_status_line, b'HTTP/2.0'
        )

        version, code, msg = Response.parse_status_line(
            b'HTTP/1.0 404 N\x99t \x0eounz\r\n')
        self.assertEqual('HTTP/1.0', version)
        self.assertEqual(404, code)
        self.assertEqual(b'N\x99t \x0eounz'.decode('latin-1'), msg)

    def test_copy(self):
        request = Request('http://twitcharchivestheinternet.invalid/')

        # Cheeck for no crash
        request.copy()
