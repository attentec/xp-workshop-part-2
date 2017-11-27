"""Simple RPC based on 0MQ, zlib, and pickle."""

import io
import pickle
import zlib

import zmq

_SAFE_TYPES = {
  'adapter_zmq': {
    'Empty',
  },
  'domain': {
    'Color',
    'Map',
    'Player',
    '_Vector',
  },
}

class _RestrictedUnpickler(pickle.Unpickler):
  def find_class(self, module, name):
    if name in _SAFE_TYPES.get(module, set()):
      return getattr(__import__(module), name)
    else:
      raise pickle.UnpicklingError("global '%s.%s' is forbidden" %
                                   (module, name))

def _serialize(x):
  p = pickle.dumps(x, protocol=3)
  z = zlib.compress(p)
  return z

def _desereialize(z):
  p = zlib.decompress(z)
  x = _RestrictedUnpickler(io.BytesIO(p)).load()
  return x

class ServerConnection:
  def __init__(self, host, port):
    self.__context = zmq.Context()
    self.__command_socket = self.__context.socket(zmq.REQ)
    self.__command_socket.connect('tcp://{}:{}'.format(host, port))

  def request(self, command_name, input=None):
    input_msg = {'command': command_name,
                  'data': input}
    self.__command_socket.send(_serialize(input_msg))
    output_msg = _desereialize(self.__command_socket.recv())
    if not output_msg['successful']:
      raise Exception('Command {} failed'.format(command_name))
    return output_msg['data']

class Server:
  def __init__(self, port):
    self.__context = zmq.Context()
    self.__command_socket = self.__context.socket(zmq.REP)
    self.__command_socket.bind('tcp://*:{}'.format(port))

  def serve(self, handler):
    input_msg = _desereialize(self.__command_socket.recv())
    command_name = input_msg['command']
    input = input_msg['data']
    try:
      fn = getattr(handler, 'handle_{}_command'.format(command_name))
      output = fn(input)
      output_msg = {'successful': True,
                     'data': output}
    except:
      output_msg = {'successful': False}
    self.__command_socket.send(_serialize(output_msg))
