import os


# pylint: disable=too-few-public-methods
class FritzboxConfig:
  """the server address of the Fritzbox (ip or name)"""
  server = "fritz.box"
  """the port the Fritzbox webserver runs on"""
  port = None  # defaults to 80 for use_tls=False, 443 for use_tls=True
  """the user name to log into the Fritzbox webinterface"""
  user = ""
  """the password to log into the Fritzbox webinterface"""
  password = ""
  use_tls = False
  certificate_file = False
  timeout = 60

  def __init__(self):
    if os.getenv('fritzbox_ip'):
      self.server = str(os.getenv('fritzbox_ip'))
    if os.getenv('fritzbox_port'):
      self.port = int(os.getenv('fritzbox_port'))
    self.user = str(os.getenv('fritzbox_user'))
    self.password = str(os.getenv('fritzbox_password'))
    if os.getenv('fritzbox_certificate') and os.path.isfile(os.getenv('fritzbox_certificate')):
      self.certificate_file = str(os.getenv('fritzbox_certificate'))
    elif os.path.isfile(str(os.getenv('MUNIN_CONFDIR')) + '/box.cer'):
      self.certificate_file = str(os.getenv('MUNIN_CONFDIR')) + '/box.cer'
    if os.getenv('fritzbox_use_tls'):
      self.use_tls = str(os.getenv('fritzbox_use_tls')) == 'true'
