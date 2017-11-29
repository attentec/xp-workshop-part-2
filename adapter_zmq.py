import enum
import traceback

import zmq

from domain import Direction, Map, Material, Object, Player, Position

NoneType = type(None)

_COMMAND_TYPES = {
  'activate': (str, NoneType),
  'get_world_map': (NoneType, Map),
  'join': (str, Player),
  'leave': (str, NoneType),
  'move': (Player, NoneType),
}

_EVENT_TYPES = {
  'player': Player,
  'player_left': str,
  'world_map': Map,
}

def serialize(Type, v):
  assert isinstance(v, Type), "{} is not a {}".format(v, Type)
  if Type in [float, int, NoneType, str]:
    return v
  elif issubclass(Type, enum.Enum):
    return v.name
  elif Type in [Direction, Position]:
    return [serialize(float, v.x), serialize(float, v.y)]
  elif Type == Map:
    return dict(materials=[serialize(Material, m) for m in v.materials],
                objects=[[serialize(Object, o), serialize(Position, p)] for o, p in v.objects],
                width=serialize(int, v.width))
  elif Type == Player:
    return dict(name=serialize(str, v.name),
                position=serialize(Position, v.position),
                forward=serialize(Direction, v.forward))
  else:
    raise Exception("Cannot serialize object of type {}".format(Type))

def deserialize(Type, v):
  if Type in [float, int, NoneType, str]:
    result = v
  elif issubclass(Type, enum.Enum):
    result = Type[v]
  elif Type in [Direction, Position]:
    x, y = v
    result = Type(x=deserialize(float, x),
                  y=deserialize(float, y))
  elif Type == Map:
    result = Map(materials=[deserialize(Material, m) for m in v['materials']],
                 objects=[(deserialize(Object, o), deserialize(Position, p)) for o, p in v['objects']],
                 width=deserialize(int, v['width']))
  elif Type == Player:
    result = Player(name=deserialize(str, v['name']),
                    position=deserialize(Position, v['position']),
                    forward=deserialize(Direction, v['forward']))
  else:
    raise Exception("Cannot deserialize object of type {}".format(Type))
  assert isinstance(result, Type), "{} is not a {}".format(v, Type)
  return result

class ServerConnection:
  def __init__(self, host, port):
    self.__context = zmq.Context()
    self.__commands = self.__context.socket(zmq.REQ)
    self.__commands.connect("tcp://{}:{}".format(host, port))
    self.__events = self.__context.socket(zmq.SUB)
    self.__events.connect("tcp://{}:{}".format(host, port + 1))
    self.__events.setsockopt_string(zmq.SUBSCRIBE, "")

  def call(self, command_name, input_data=None):
    InputType, OutputType = _COMMAND_TYPES[command_name]
    input_json = {'command': command_name,
                  'input': serialize(InputType, input_data)}
    self.__commands.send_json(input_json)
    output_json = self.__commands.recv_json()
    assert output_json['success']
    output_data = deserialize(OutputType, output_json['output'])
    return output_data

  def poll_events(self):
    while True:
      try:
        event_json = self.__events.recv_json(flags=zmq.NOBLOCK)
        event_name = event_json['event']
        EventType = _EVENT_TYPES[event_name]
        event_data = deserialize(EventType, event_json['data'])
        yield event_name, event_data
      except zmq.ZMQError as e:
        if e.errno == zmq.EAGAIN:
          break
        else:
          raise

class Server:
  def __init__(self, port):
    self.__context = zmq.Context()
    self.__commands = self.__context.socket(zmq.REP)
    self.__commands.bind("tcp://*:{}".format(port))
    self.__events = self.__context.socket(zmq.PUB)
    self.__events.bind("tcp://*:{}".format(port + 1))

  def serve(self, command_fn):
    while True:
      input_json = self.__commands.recv_json()
      command_name = input_json['command']
      InputType, OutputType = _COMMAND_TYPES[command_name]
      input_data = deserialize(InputType, input_json['input'])
      try:
        output_data = command_fn(command_name, input_data)
        output_json = {'success': True,
                       'output': serialize(OutputType, output_data)}
      except:
        traceback.print_exc()
        output_json = {'success': False}
      self.__commands.send_json(output_json)

  def emit_event(self, event_name, event_data):
    EventType = _EVENT_TYPES[event_name]
    event_json = {'event': event_name,
                  'data': serialize(EventType, event_data)}
    self.__events.send_json(event_json)
