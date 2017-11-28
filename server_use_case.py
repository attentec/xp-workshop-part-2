from collections import namedtuple
from random import randint

_State = namedtuple('_State', 'player_spawn, world_map, players')

def initial_state(player_spawn, world_map):
  return _State(player_spawn, world_map, {})

def handle_command(state, command_name, input_data):
  output_data = None
  events = []
  if command_name == 'leave':
    name = input_data
    del state.players[name]
    events.append(('player_left', name))
    print("Player left: " + name)
  elif command_name == 'get_world_map':
    output_data = state.world_map
  elif command_name == 'new_player':
    name = input_data
    player = state.player_spawn._replace(name=name)
    state.players[name] = player
    output_data = player
    events.append(('player', player))
    print("New player: " + name)
  else:
    raise NotImplementedError()
  return state, output_data, events
