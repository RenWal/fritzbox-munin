#!/usr/bin/env python3
"""
  FritzboxInterface - A munin plugin for Linux to monitor AVM Fritzbox
  Copyright (C) 2015 Christian Stade-Schuldt
  Copyright (C) 2021 Rene Walendy
  Copyright (c) 2021 Oliver Edelmann
  Author: Christian Stade-Schuldt, Rene Walendy
  Like Munin, this plugin is licensed under the GNU GPL v2 license
  http://www.opensource.org/licenses/GPL-2.0

  Add the following section to your munin-node's plugin configuration:

  [fritzbox_*]
  env.fritzbox_ip [ip address of the fritzbox]
  env.fritzbox_password [fritzbox password]
  env.fritzbox_user [fritzbox user, set any value if not required]
  env.fritzbox_use_tls [true or false, optional]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf

  The initial script was inspired by
  https://www.linux-tips-and-tricks.de/en/programming/389-read-data-from-a-fritzbox-7390-with-python-and-bash
  framp at linux-tips-and-tricks dot de
"""

import hashlib
import sys
import json

from typing import Callable
from json.decoder import JSONDecodeError
import requests
from lxml import etree
from FritzboxConfig import FritzboxConfig
from fritzbox_file_session import FritzboxFileSession

class FritzboxInterface:
  config = None
  __session = None
  __base_uri = ""

  # default constructor
  def __init__(self, config: FritzboxConfig = None, session: FritzboxFileSession = None):
    self.config = config if (config) else FritzboxConfig()
    self.__session = session if (session) else FritzboxFileSession(self.config.server, self.config.user, self.config.port)
    self.__base_uri = self.__get_base_uri()

  def __get_base_uri(self) -> str:
    default_ports = (80, 443)
    schemes = ('http', 'https')
    if self.config.port and self.config.port != default_ports[self.config.useTls]:
      return f"{schemes[self.config.useTls]}://{self.config.server}:{self.config.port}"

    return f"{schemes[self.config.useTls]}://{self.config.server}"

  def get_page_with_login(self, page: str, data={}) -> str:
    return self.__call_page_with_login(self.__get, page, data)

  def post_page_with_login(self, page: str, data={}) -> dict:
    data = self.__call_page_with_login(self.__post, page, data)

    try:
      json_data = json.loads(data)
    except JSONDecodeError as json_exception:
      # Perhaps session expired, let's clear the session and try again
      self.__session.clear_session()
      sys.exit('ERROR: Did not receive valid JSON data from FritzBox, so automatically cleared the session, please try again.: ' + str(json_exception))

    return json_data

  # Code from https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/AVM_Technical_Note_-_Session_ID_deutsch_2021-05-03.pdf
  def __calculate_pbkdf2_response(self, challenge) -> str:
    """ Calculate the response for a given challenge via PBKDF2 """
    challenge_parts = challenge.split("$")
    # Extract all necessary values encoded into the challenge
    iter1 = int(challenge_parts[1])
    salt1 = bytes.fromhex(challenge_parts[2])
    iter2 = int(challenge_parts[3])
    salt2 = bytes.fromhex(challenge_parts[4])
    # Hash twice, once with static salt...
    # Once with dynamic salt.
    hash1 = hashlib.pbkdf2_hmac("sha256", self.config.password.encode(), salt1, iter1)
    hash2 = hashlib.pbkdf2_hmac("sha256", hash1, salt2, iter2)
    return f"{challenge_parts[4]}${hash2.hex()}"

  # Code from https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/AVM_Technical_Note_-_Session_ID_deutsch_2021-05-03.pdf
  def __calculate_md5_response(self, challenge) -> str:
    """ Calculate the response for a challenge using legacy MD5 """
    response = challenge + "-" + self.config.password
    # the legacy response needs utf_16_le encoding
    response = response.encode("utf_16_le")
    md5_sum = hashlib.md5()
    md5_sum.update(response)
    response = challenge + "-" + md5_sum.hexdigest()
    return response

  def __get_session_id(self) -> str:
    """Obtains the session id after login into the Fritzbox.
    See https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/AVM_Technical_Note_-_Session_ID.pdf
    for details (in German).

    :return: the session id
    """

    headers = {"Accept": "application/xml", "Content-Type": "text/plain"}

    url = f"{self.__base_uri}/login_sid.lua?version=2"
    try:
      result = requests.get(url, headers=headers, verify=self.config.certificateFile)
      result.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.SSLError) as err:
      print(err)
      sys.exit(1)

    params = {}
    root = etree.fromstring(result.content)
    session_id = root.xpath('//SessionInfo/SID/text()')[0]
    if session_id == "0000000000000000":
      challenge = root.xpath('//SessionInfo/Challenge/text()')[0]
      if challenge.startswith("2$"): # we received a PBKDF2 challenge
        response_bf = self.__calculate_pbkdf2_response(challenge)
      else: # or fall back to MD5
        response_bf = self.__calculate_md5_response(challenge)
      params['response'] = response_bf
    else:
      return session_id

    params['username'] = self.config.user

    headers = {"Accept": "text/html,application/xhtml+xml,application/xml", "Content-Type": "application/x-www-form-urlencoded"}

    url = f"{self.__base_uri}/login_sid.lua"
    try:
      result = requests.get(url, headers=headers, params=params, verify=self.config.certificateFile)
      result.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.SSLError) as err:
      print(err)
      sys.exit(1)

    root = etree.fromstring(result.content)

    session_id = root.xpath('//SessionInfo/SID/text()')[0]
    if session_id == "0000000000000000":
      print("ERROR: No SID received because of invalid credentials")
      sys.exit(0)

    self.__session.save_session_id(session_id)

    return session_id

  def __call_page_with_login(self, method: Callable[[], str], page, data={}) -> str:
    session_id = self.__session.load_session_id()

    if session_id is not None:
      try:
        return method(session_id, page, data)
      except (requests.exceptions.HTTPError,
             requests.exceptions.SSLError) as request_exception:
        code = request_exception.response.status_code
        if code != 403:
          print(request_exception)
          sys.exit(1)

    session_id = self.__get_session_id()
    return method(session_id, page, data)

  def __post(self, session_id, page, data={}) -> str:
    """Sends a POST request to the Fritzbox and returns the response

    :param session_id: a valid session id
    :param page: the page you are requesting
    :param data: POST data in a map
    :return: the content of the page
    """

    data['sid'] = session_id

    headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}

    url = f"{self.__base_uri}/{page}"

    result = requests.post(url, headers=headers, data=data, verify=self.config.certificateFile)
    result.raise_for_status()

    return result.content

  def __get(self, session_id, page, data={}) -> str:
    """Fetches a page from the Fritzbox and returns its content

    :param session_id: a valid session id
    :param page: the page you are requesting
    :param params: GET parameters in a map
    :return: the content of the page
    """

    headers = {"Accept": "application/xml", "Content-Type": "text/plain"}

    params = data
    params["sid"] = session_id
    url = f"{self.__base_uri}/{page}"

    result = requests.get(url, headers=headers, params=params, verify=self.config.certificateFile)
    result.raise_for_status()

    return result.content
