#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Copyright (C) 2023 Paco8
    based on NFAuthenticationKey:
    Copyright (C) 2020 Stefano Gottardo
    SPDX-License-Identifier: GPL-3.0-only
    See LICENSE.md for more information.
"""
import base64
import json
import os
import platform
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta

import websocket  # pip install websocket-client

try:  # Python 3
    from urllib.request import HTTPError, URLError, urlopen
except ImportError:  # Python 2
    from urllib2 import HTTPError, URLError, urlopen

IS_MACOS = platform.system().lower() == 'darwin'
IS_WINDOWS = platform.system().lower() == 'windows'

# Script configuration
BROWSER_PATH = '* Remove me and specify here the browser path, only if not recognized *'
DEBUG_PORT = 9222
LOCALHOST_ADDRESS = 'localhost'

HOST = 'https://www.peacocktv.com'
URL = HOST + '/signin'
OUTPUT_KEY = 'peacock.key'

def select_platform(platform):
  global HOST, URL, OUTPUT_KEY
  if platform == 'peacock':
    HOST = 'https://www.peacocktv.com'
    OUTPUT_KEY = 'peacock.key'
  else:
    HOST = 'https://www.skyshowtime.com'
    OUTPUT_KEY = 'skyshowtime.key'
  URL = HOST + '/signin'


class Main(object):

    app_version = '1.0.3'
    _msg_id = 0
    _ws = None

    def __init__(self, browser_temp_path):
        show_msg('')
        show_msg('SkyExtractCookie for Linux/MacOS/Windows (Version {})'.format(self.app_version),
                 TextFormat.COL_LIGHT_BLUE + TextFormat.BOLD)
        show_msg('')
        show_msg('Disclaimer:')
        show_msg(
            'This script and source code available on GitHub are provided "as is" without\r\n'
            'warranty of any kind, either express or implied. Use at your own risk. The use\r\n'
            'of the software is done at your own discretion and risk with the agreement\r\n'
            'that you will be solely responsible for any damage resulting from such\r\n'
            'activities and you are solely responsible for adequate data protection.',
            TextFormat.COL_GREEN)
        show_msg('')
        browser_proc = None
        try:
            input_msg('Press "ENTER" key to accept the disclaimer and start, or "CTRL+C" to cancel', TextFormat.BOLD)
            k = None
            while k not in ['1', '2']:
              k = input_msg('\r\nWould you like to extract the cookie for PeacockTV or SkyShowTime?\r\n1) PeacockTV\r\n2) SkyShowtime\r\n', TextFormat.BOLD)
              if k == '1': select_platform('peacock')
              if k == '2': select_platform('skyshowtime')
            #print(HOST, URL, OUTPUT_KEY)
            #quit()
            browser_proc = open_browser(browser_temp_path)
            self.operations()
        except Warning as exc:
            show_msg(str(exc), TextFormat.COL_LIGHT_RED)
            if browser_proc:
                browser_proc.terminate()
        except Exception as exc:
            show_msg('An error occurred:\r\n' + str(exc), TextFormat.COL_LIGHT_RED)
            import traceback
            show_msg(traceback.format_exc())
            if browser_proc:
                browser_proc.terminate()
        finally:
            try:
                if self._ws:
                    self._ws.close()
            except Exception:
                pass

    def operations(self):
        show_msg('Establish connection with the browser in port {}... please wait'.format(DEBUG_PORT))
        self.get_browser_debug_endpoint()
        self.ws_request('Network.enable')
        self.ws_request('Page.enable')
        show_msg('Opening login webpage... please wait')
        self.ws_request('Page.navigate', {'url': URL})

        self.ws_wait_event('Page.domContentEventFired')  # Wait loading DOM (document.onDOMContentLoaded event)

        show_msg('Please login in to website now ...waiting for you to finish...', TextFormat.COL_LIGHT_BLUE)

        res = self.wait_login()
        if not res:
            raise Warning('You have exceeded the time available for the login. Try again.')

        show_msg('File creation in progress... please wait')

        # Create file data structure
        data = {
            'app_name': 'SkyExtractCookie',
            'app_version': self.app_version,
            'app_system': 'Windows' if IS_WINDOWS else 'MacOS' if IS_MACOS else 'Linux',
            'timestamp': int(time.time()*1000),
            'data': json.dumps(res, ensure_ascii=False),
            'host': HOST
        }
        # Save the key file
        save_data(data)
        # Close the browser
        self.ws_request('Browser.close')
        show_msg('Done!', TextFormat.COL_BLUE)
        show_msg('The {} file has been saved in the current folder.'.format(OUTPUT_KEY), TextFormat.COL_BLUE)


    def get_browser_debug_endpoint(self):
        start_time = time.time()
        while time.time() - start_time < 15:
            try:
                endpoint = ''
                data = urlopen('http://{0}:{1}/json'.format(LOCALHOST_ADDRESS, DEBUG_PORT), timeout=1).read().decode('utf-8')
                if not data:
                    raise ValueError
                session_list = json.loads(data)
                for item in session_list:
                    if item['type'] == 'page':
                        endpoint = item['webSocketDebuggerUrl']
                if not endpoint:
                    raise Warning('Chrome session page not found')
                self._ws = websocket.create_connection(endpoint)
                return
            except (URLError, socket.timeout, ValueError):  # json.JSONDecodeError inherited ValueError and available from >= py3.5
                pass
        raise Warning('Unable to connect with the browser')

    def wait_login(self):
        req_id = self.msg_id
        res = None
        start_time = time.time()
        request_id = None
        while time.time() - start_time < 300:  # 5 min
            message = self._ws.recv()
            parsed_message = json.loads(message)
            if 'method' in parsed_message:
                if parsed_message['method'] == 'Network.requestWillBeSentExtraInfo':
                    if 'headers' in parsed_message['params']:
                        if ':path' in parsed_message['params']['headers']:
                            if '/watch/home' in parsed_message['params']['headers'][':path']:
                                #print('m: {}'.format(json.dumps(parsed_message, indent=4)))
                                res = parsed_message['params']['headers']['cookie']
                                break
        return res

    @property
    def msg_id(self):
        self._msg_id += 1
        return self._msg_id

    @msg_id.setter
    def msg_id(self, value):
        self._msg_id = value

    def ws_request(self, method, params=None):
        req_id = self.msg_id
        message = json.dumps({'id': req_id, 'method': method, 'params': params or {}})
        self._ws.send(message)
        start_time = time.time()
        while True:
            if time.time() - start_time > 10:
                break
            message = self._ws.recv()
            parsed_message = json.loads(message)
            if 'result' in parsed_message and parsed_message['id'] == req_id:
                return parsed_message['result']
        raise Warning('No data received from browser')

    def ws_wait_event(self, method):
        start_time = time.time()
        while True:
            if time.time() - start_time > 10:
                break
            message = self._ws.recv()
            parsed_message = json.loads(message)
            if 'method' in parsed_message and parsed_message['method'] == method:
                return parsed_message
        raise Warning('No event data received from browser')


# Helper methods
class TextFormat:
    """Terminal color codes"""
    COL_BLUE = '\033[94m'
    COL_GREEN = '\033[92m'
    COL_LIGHT_YELLOW = '\033[93m'
    COL_LIGHT_RED = '\033[91m'
    COL_LIGHT_BLUE = '\033[94m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def open_browser(browser_temp_path):
    params = ['--incognito',
              '--user-data-dir={}'.format(browser_temp_path),
              '--remote-debugging-port={}'.format(DEBUG_PORT),
              '--no-first-run',
              '--no-default-browser-check',
              '--remote-allow-origins=*',
              #'--proxy-server=127.0.0.1:18080'
             ]
    dev_null = open(os.devnull, 'wb')
    try:
        browser_path = get_browser_path()
        show_msg('Browser startup... ({}) please wait'.format(browser_path))
        return subprocess.Popen([browser_path] + params, stdout=dev_null, stderr=subprocess.STDOUT)
    finally:
        dev_null.close()


def get_browser_path():
    """Check and return the name of the installed browser"""
    if '*' not in BROWSER_PATH:
        return BROWSER_PATH

    if IS_WINDOWS:
        for browser_name in ['Google\\Chrome\\Application\\chrome.exe', 'Chromium\\Application\\chromium.exe', 'BraveSoftware\\Brave-Browser\\Application\\brave.exe']:
            for dir in ['C:\\Program Files\\', 'C:\\Program Files (x86)\\']:
                path = dir + browser_name
                if os.path.exists(path):
                    return path
    elif IS_MACOS:
        for browser_name in ['Google Chrome', 'Chromium', 'Brave Browser']:
            path = '/Applications/' + browser_name + '.app/Contents/MacOS/' + browser_name
            if os.path.exists(path):
                return path
    else:
        for browser_name in ['google-chrome', 'google-chrome-stable', 'google-chrome-unstable', 'chromium', 'chromium-browser', 'brave-browser', 'brave']:
            try:
                path = subprocess.check_output(['which', browser_name]).decode('utf-8').strip()
                if path:
                    return path
            except subprocess.CalledProcessError:
                pass
    raise Warning('Browser not detected.\r\nCheck if it is installed or specify the path in settings.json, in the field browser-path')


def save_data(data):
    data = json.dumps(data, ensure_ascii=False)
    file = open(OUTPUT_KEY, 'w')
    file.write(data)
    file.close()


def show_msg(text, text_format=None):
    if text_format and not IS_WINDOWS:
        text = text_format + text + TextFormat.END
    print(text)


def input_msg(text, text_format=None):
    if text_format and not IS_WINDOWS:
        text = text_format + text + TextFormat.END
    if sys.version_info.major == 2:
        return raw_input(text)
    else:
        return input(text)


if __name__ == '__main__':
    temp_path = tempfile.mkdtemp()

    try:
      if os.path.exists('settings.json'):
        with open('settings.json', 'r') as file:
          d = json.load(file)
          if d.get('browser-path'):
            BROWSER_PATH = d['browser-path']
          if d.get('debug-port'):
            DEBUG_PORT = d['debug-port']
    except:
      pass

    try:
        Main(temp_path)
    except KeyboardInterrupt:
        show_msg('\r\nOperations cancelled')
    finally:
        try:
            shutil.rmtree(temp_path)
        except Exception:
            pass

    if IS_WINDOWS:
        input_msg('Press "Enter" to finish', TextFormat.BOLD)
