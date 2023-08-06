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
  useTls = True
  certificateFile = str(os.getenv('MUNIN_CONFDIR')) + '/box.cer'

  def __init__(self,
               fritzbox_ip          = None,
               fritzbox_port        = None,
               fritzbox_user        = None,
               fritzbox_password    = None,
               fritzbox_certificate = None,
               fritzbox_useTls      = None,
               ):
    if fritzbox_ip is None:
      if os.getenv('fritzbox_ip'):
        self.server = str(os.getenv('fritzbox_ip'))
      # end if
    else:
        self.server = fritzbox_ip
    # end if
        
    if fritzbox_port is None:
      if os.getenv('fritzbox_port'):
        self.port = int(os.getenv('fritzbox_port'))
      # end if
    else:
        self.port = fritzbox_port
    # end if

    if fritzbox_user is None:
      self.user = str(os.getenv('fritzbox_user'))
    else:
      self.user = fritzbox_user
    # endif
      
    if fritzbox_password is None:
      self.password = str(os.getenv('fritzbox_password'))
    else:
      self.password = fritzbox_password
    # endif
    
    if fritzbox_certificate is None:
      if os.getenv('fritzbox_certificate'):
        self.certificateFile = str(os.getenv('fritzbox_certificate'))
      # endif
    else:
      self.certificateFile = fritzbox_certificate
    # endif

    if fritzbox_useTls is None:
      if os.getenv('fritzbox_use_tls'):
        self.useTls = str(os.getenv('fritzbox_use_tls')) == 'true'
      # endif
    else:
      self.useTls = fritzbox_use_tls
    # endif
  
  # end __init__
# end class  FritzboxConfig

