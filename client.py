import argparse
from getpass import getuser
import os.path
import sys

from adapter_pygame import Color, milliseconds_since_start, load_color_scheme, load_font, load_image, load_map, load_player_spawn, load_images_for_enum, process_input, Renderer
from adapter_zmq import ServerConnection
from domain import Angle, Direction, initial_input, Map, Material, Player, Position, Object
from use_case import initial_state, handle_event

def main(args):
  root = os.path.dirname(os.path.realpath(__file__))
  map_path = os.path.join(root, 'map')

  if args.connect:
    server = ServerConnection(args.connect, args.port)
    player = server.call("join", getuser())
    other_players = {}
    world_map = server.call("get_world_map")
  else:
    server = None
    player = load_player_spawn(map_path)
    other_players = {}
    world_map = load_map(map_path)

  color_scheme = load_color_scheme(map_path)
  objects = load_images_for_enum(os.path.join(root, 'object'), Object)
  materials = load_images_for_enum(os.path.join(root, 'material'), Material)
  player_texture = load_image(os.path.join(root, 'player.png'))
  font = load_font(os.path.join(root, 'font', 'league_mono', 'LeagueMono-Light.otf'), size=18)

  renderer = Renderer(
    window_size=(640, 480),
    materials=materials,
    objects=objects,
    player_texture=player_texture,
    font=font,
    field_of_view=Angle.from_degrees(66),
    draw_distance=100,
    far_color=Color(red=0, green=0, blue=0),
    shade_scale=0.85,
    object_scale=0.75
  )

  max_frame_time = 50
  rotation_speed = 3
  movement_speed = 5

  time = milliseconds_since_start()
  input = initial_input
  state = initial_state(input, player, world_map, rotation_speed, movement_speed)
  running = True

  while running:
    if server:
      for event_name, data in server.poll_events():
        if event_name == "world_map":
          state = state._replace(world_map=data)
        if event_name == "player":
          if data.name != player.name:
            other_players[data.name] = data
        if event_name == "player_left":
          if data in other_players:
            del other_players[data]

    last_time = time
    time = milliseconds_since_start()
    frame_time = min(time - last_time, max_frame_time) / 1000

    (input, running) = process_input(previous_input=input)
    old_player = state.player
    state, _ = handle_event(state, 'input', input)
    state, _ = handle_event(state, 'tick', frame_time)
    renderer.draw(color_scheme, state.world_map, state.player, other_players.values())
    if server and state.player != old_player:
      server.call('move', state.player)
  if server:
    server.call('leave', state.player.name)

  return 0

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("--connect")
  parser.add_argument("--port", type=int, default=12345)
  args = parser.parse_args()
  sys.exit(main(args))
