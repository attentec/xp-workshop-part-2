from collections import namedtuple

_State = namedtuple('_State', 'player_spawn, world_map')

def initial_state(player_spawn, world_map):
  return _State(player_spawn, world_map)

def handle_command(state, command_name, input_data):
  output_data = None
  events = []
  if command_name == 'new_player':
    output_data = state.player_spawn
  elif command_name == 'request_world_map':
    events.append(('world_map', state.world_map))
  else:
    raise NotImplementedError()
  return state, output_data, events
