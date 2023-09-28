import os

class FritzboxConfig:
  """the server address of the Fritzbox (ip or name)"""
  server = "fritz.box"
  """the port the Fritzbox webserver runs on"""
  port = None # defaults to 80 for useTls=False, 443 for useTls=True
  """the user name to log into the Fritzbox webinterface"""
  user = ""
  """the password to log into the Fritzbox webinterface"""
  password = ""
  use_tls = True
  certificate_file = str(os.getenv('MUNIN_CONFDIR')) + '/box.cer'

  def __init__(self):
    if os.getenv('fritzbox_ip'):
      self.server = str(os.getenv('fritzbox_ip'))
    if os.getenv('fritzbox_port'):
      self.port = int(os.getenv('fritzbox_port'))
    self.user = str(os.getenv('fritzbox_user'))
    self.password = str(os.getenv('fritzbox_password'))
    if os.getenv('fritzbox_certificate'):
      self.certificate_file = str(os.getenv('fritzbox_certificate'))
    if os.getenv('fritzbox_use_tls'):
      self.use_tls = str(os.getenv('fritzbox_use_tls')) == 'true'
