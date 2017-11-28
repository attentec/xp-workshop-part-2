from collections import namedtuple

from domain import Angle, find_first_collision, initial_input, LineSegment, Player, Position

_State = namedtuple('State', 'input, player, world_map, rotation_speed, movement_speed, other_players')

def rotate_player(player, input, frame_time, speed):
  rotation_sign = (1 if input.turn_right else 0) - (1 if input.turn_left else 0)

  if rotation_sign == 0:
    return player

  rotation_delta = Angle.from_radians(rotation_sign * speed * frame_time)
  new_forward = player.forward.rotate(rotation_delta)
  return player._replace(forward=new_forward)

def _try_to_move(map, from_, to):
  return to if find_first_collision(map, LineSegment(from_, to)) is None else from_

def move_player(player, map, input, frame_time, speed):
  movement_sign = (1 if input.forward else 0) - (1 if input.backward else 0)

  if movement_sign == 0:
    return player

  movement_delta = player.forward*(movement_sign * speed * frame_time)
  new_position = Position(player.position.x, player.position.y)

  x_target = Position(new_position.x + movement_delta.x, new_position.y)
  new_position = _try_to_move(map, from_=new_position, to=x_target)

  y_target = Position(new_position.x, new_position.y + movement_delta.y)
  new_position = _try_to_move(map, from_=new_position, to=y_target)

  return player._replace(position=new_position)

def initial_state(initial_input, player, world_map, rotation_speed, movement_speed):
  return _State(initial_input, player, world_map, rotation_speed, movement_speed, {})

def handle_event(state, event_name, event_data):
  commands = []
  if event_name == 'tick':
    frame_time = event_data
    player = state.player
    player = rotate_player(player, state.input, frame_time, state.rotation_speed)
    player = move_player(player, state.world_map, state.input, frame_time, state.movement_speed)
    state = state._replace(player=player)
  elif event_name == 'input':
    new_input = event_data
    if new_input.activate and not state.input.activate:
      commands.append(('activate', state.player.name))
    state = state._replace(input=new_input)
  elif event_name == 'world_map':
    state = state._replace(world_map=event_data)
  elif event_name == 'player':
    other_player = event_data
    if other_player.name != state.player.name:
      state.other_players[other_player.name] = other_player
  elif event_name == 'player_left':
    other_player_name == event_data
    if other_player_name in state.other_players:
      del state.other_players[other_player_name]
  else:
    # TODO: implement more events
    pass
  return state, commands
