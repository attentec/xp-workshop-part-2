from domain import Material

from collections import namedtuple
from random import randint

_State = namedtuple('_State', 'player_spawn, world_map, links, players')

def initial_state(player_spawn, world_map, links):
  return _State(player_spawn, world_map, links, {})

def handle_command(state, command_name, input_data):
  output_data = None
  events = []
  if command_name == 'activate':
    player_name = input_data
    assert player_name in state.players
    player = state.players[player_name]
    key_pos = player.position.to_grid()
    door_pos = state.links.get(key_pos, None)
    if door_pos:
      new_material = Material.DOOR if state.world_map.material(door_pos) == Material.FLOOR else Material.FLOOR
      new_world_map = state.world_map.replace_material(door_pos, new_material)
      state = state._replace(world_map=new_world_map)
      events.append(('world_map', new_world_map))
  elif command_name == 'get_world_map':
    output_data = state.world_map
  elif command_name == 'join':
    name = input_data
    if name not in state.players:
      player = state.player_spawn._replace(name=name)
    else:
      player = state.players[name]
    state.players[name] = player
    for player in state.players.values():
      events.append(('player', player))
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
