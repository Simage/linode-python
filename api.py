#!/usr/bin/python
"""
A Python library to perform low-level Linode API functions.

Copyright (c) 2008 Timothy J Fontaine <tjfontaine@gmail.com>
Copyright (c) 2008 James C Sinclair <james@irgeek.com>

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import urllib
import urllib2
import simplejson

class MissingRequiredArgument(Exception):
  """Raised when a required parameter is missing."""
  
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class ApiError(Exception):
  """Raised when a Linode API call returns an error."""
  
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class Api:
  def __init__(self, key):
    self.__key = key
    self.__url = 'http://beta.linode.com/api/'
    self.__urlopen = urllib2.urlopen
    self.__request = urllib2.Request

  def __send_request(self, request):
    request['api_key'] = self.__key
    request['resultFormat'] = 'json'
    request = urllib.urlencode(request)
    req = self.__request(self.__url,request)
    response = self.__urlopen(req)
    response = response.read()
    json = simplejson.loads(response)
    if len(json['ERRORARRAY']) > 0:
      raise ApiError(json['ERRORARRAY'])
    return json['DATA']

  def __simple_decorator(decorator):
    def new_decorator(f):
      g = decorator(f)
      g.__name__ = f.__name__
      g.__doc__ = f.__doc__
      g.__dict__.update(f.__dict__)
      return g
    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)
    return new_decorator

  @__simple_decorator
  def __api_request(func):
    def decorator(self, *__args, **__kw):
      request = {'action' : func.__name__}
      for k in __kw: request[k] = __kw[k]
      if len(__args) == 1:
        for k in __args[0]: request[k] = __args[0][k]
      result = func(self, request)
      if result is not None:
        request = result
      return self.__send_request(request)
    return decorator

  def __api_required(*args, **kw):
    def decorator(func):
      def wrapper(*__args,**__kw):
        for k in args:
          if not __kw.has_key(k) and (len(__args) == 2 and not __args[1].has_key(k)):
            raise MissingRequiredArgument(k)
        return func(*__args,**__kw)
      wrapper.__name__ = func.__name__
      wrapper.__doc__ = func.__doc__
      wrapper.__dict__.update(func.__dict__)
      return wrapper
    return decorator

  @__api_request
  def domainList(self, request):
    """Retrieve the list of domains visible to the user.

    Parameters:
      None

    Returns an array of hashes, one per domain, each with the following fields:
      DOMAINID       - Unique identifier for the domain
      DOMAIN         - Domain's name e.g. 'linode.com'
      TYPE           - Domain's type: 'master' or 'slave'
      STATUS         - Domain's current status
        * Possible values are listed below
      SOA_EMAIL      - SOA email address for the domain
      REFRESH_SEC *  - 'refresh' value for the domain
        * A value of zero indicates default time (2 hours)
      RETRY_SEC *    - 'retry' value for the domain
        * A value of zero indicates default time (2 hours)
      TTL_SEC *      - 'ttl' value for the domain
        * A value of zero indicates default time (1 day)

    Possible values for STATUS
      0 - Disabled   - Domain is not being served
      1 - Active     - Domain is being served
      2 - Edit Mode  - Domain is being served but changes are not rendered
      3 - Has Errors - There are errors in the rendered zonefile
    
    """

  @__api_required('DomainID')
  @__api_request
  def domainGet(self, request):
    """Retrieve the details for a specific domain.

    Parameters:
      DomainID       - Unique identifier for the domain to be retrieved
        * Always required

    Returns a hash for the requested domain
      * See domainList documentation for the fields in the hash
    
    """

  @__api_required('DomainID', 'Domain', 'Type', 'Status', 'SOA_Email')
  @__api_request
  def domainSave(self, request):
    """Create or update a specific domain.

    Parameters:
      DomainID       - Unique identifier for the domain
        * Always required - use 0 to insert a new domain
      Domain         - Domain's name e.g. 'linode.com'
        * Always required
      Type           - Domain's type: 'master' or 'slave'
        * Always required
      Status         - Domain's new status
        * Always required - see domainList documentation for possible values
      SOA_Email      - SOA email address for the domain
        * Always required
      Master_IPs     - Semicolon separated list of IP(s) for master servers
        * Required if Type = 'slave', ignored otherwise
      Refresh_Sec    - 'refresh' value for the domain
        * Excluding or setting to zero indicates default time (2 hours)
      Retry_Sec      - 'retry' value for the domain
        * Excluding or setting to zero indicates default time (2 hours)
      TTK_Sec        - 'ttl' value for the domain
        * Excluding or setting to zero indicates default time (1 day)

    Returned fields:
      DOMAINID       - Unique identifier for the new or updated domain

    *** Parameters not passed to update a domain will be reset to defaults ***

    """

  @__api_required('DomainID')
  @__api_request
  def domainResourceList(self, request):
    """Retrieve the list of resource records (RRs) for a specific domain.
    
    Parameters:
      DomainID       - Unique identifier for the domain
        * Always required

    Returns an array of hashes, one per RR, each with the following fields:
      RESOURCEID     - Unique identifier for the RR
      DOMAINID       - Unique identifier for the domain
      NAME           - Name of the RR
        * May be empty
      TYPE           - Type of the RR
        * Possible values are listed below
      TARGET         - IP, name or string this RR resolves to
      PRIORITY       - Priority for MX type RRs
      TTL_SEC        - 'ttl' value for the RR
        * A value of zero indicates the domain default
      WEIGHT         - Weight for SRV type RRs
      PORT           - Port for SRV type RRs
    
    Possible values for RR TYPE
      NS             - Name server
      MX             - Mail exchanger
      A              - IPv4 address
      AAAA           - IPv6 address
      CNAME          - Canonical name
      TXT            - Text
      SRV            - Service location
    
    """

  @__api_required('ResourceID')
  @__api_request
  def domainResourceGet(self, request):
    """Retrieve the details for a specific resource record (RR).

    Parameters:
      ResourceID     - Unique identifier for the domain to be retrieved
        * Always required

    Returns a hash for the requested RR
      * See domainResourceList documentation for the fields in the hash
      
    """

  @__api_required('ResourceID', 'DomainID')
  @__api_request
  def domainResourceSave(self, request):
    """Create or update a specific resource record (RR).
    
    Parameters:
      ResourceID     - Unique identifier for the RR
        * Always required - use 0 to insert a new RR
      DomainID       - Unique identifier for the domain
        * Always required.
      Name           - Name of the RR
        * May be empty
      Type           - Type of the RR
        * Always required - see domainResourceList documentation for possible values
      Target         - IP, name or string this RR resolves to
      Priority       - Priority for MX type RRs
      TTL_Sec        - 'ttl' value for the RR
        * A value of zero indicates the domain default
      Weight         - Weight for SRV type RRs
      Port           - Port for SRV type RRs
      
    Returned fields:
      RESOURCEID     - Unique identifier for the new or updated RR

    *** Parameters not passed to update an RR will be reset to defaults ***

    """

  @__api_request
  def linodeList(self, request):
    """Retrieve the list of Linodes visible to the user.
    
    Parameters:
      None
      
    Returns an array of hashes, one per Linode, each with the following fields:
      LINODEID       - The unique identifier for this Linode
      STATUS         - The Linode's status (see below)
      HOSTHOSTNAME   - The DNS name for the host the Linode is on
      LISHUSERNAME   - The username to connect to a Lish session
      LABEL          - The label for the Linode, as seen on the Linode Manager
      TOTALRAM       - Total RAM assigned to this Linode (MiB)
      TOTALHD        - Total hard drive space assigned to this Linode (MiB)
      TOTALXFER      - Total transfer assigned to this Linode (GiB)
      
    Possible values for STATUS
      * This is still an undocumented API call
      
    """

if __name__ == "__main__":
  from getpass import getpass
  import readline
  import atexit
  import os

  valid_commands = []
  for c in dir(Api):
    if c[0] != '_':
      valid_commands.append(c)

  valid_commands.append('help')
  valid_commands.append('exit')

  def complete(text, state):
    results = [x for x in valid_commands if x.startswith(text)] + [None]
    return results[state]

  readline.set_completer(complete)
  readline.parse_and_bind("tab: complete")
  
  histfile = os.path.expanduser('~/.linode-console-history')
  if hasattr(readline, "read_history_file"):
    try:
      readline.read_history_file(histfile)
    except IOError:
      pass
      atexit.register(readline.write_history_file, histfile)

  key = getpass('Enter API Key: ')
  lapi = Api(key)
  quitting = False
  
  while not quitting:
    command = raw_input('> ')
    if command.lower() == 'exit':
      quitting = True
    elif command.lower() == 'help':
      print ' '.join(valid_commands)
    elif hasattr(lapi, command):
      params = raw_input('Enter named parameters (name:param[,name2:param2]): ')
      method = getattr(lapi, command)
      keywords = {}
      if params != '':
        for p in params.split(','):
          a = p.split(':')
          keywords[a[0]] = a[1]
      ret = method(keywords)
      print simplejson.dumps(ret, indent=2)
