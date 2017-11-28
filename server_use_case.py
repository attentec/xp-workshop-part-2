from collections import namedtuple
from random import randint

_State = namedtuple('_State', 'player_spawn, world_map, players')

def initial_state(player_spawn, world_map):
  return _State(player_spawn, world_map, {})

def handle_command(state, command_name, input_data):
  output_data = None
  events = []
  if command_name == 'get_world_map':
    output_data = state.world_map
  elif command_name == 'join':
    name = input_data
    if name not in state.players:
      player = state.player_spawn._replace(name=name)
      events.append(('player', player))
    else:
      player = state.players[name]
    state.players[name] = player
    output_data = player
    print("Player joined: " + name)
  elif command_name == 'leave':
    name = input_data
    assert name in state.players
    events.append(('player_left', name))
    print("Player left: " + name)
  elif command_name == 'move':
    player = input_data
    assert player.name in state.players
    state.players[player.name] = player
    events.append(('player', player))
  else:
    raise NotImplementedError()
  return state, output_data, events
