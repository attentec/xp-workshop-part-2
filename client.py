import argparse
import os.path
import sys

from adapter_pygame import Color, milliseconds_since_start, load_color_scheme, load_map, load_player_spawn, load_images_for_enum, process_input, Renderer
from adapter_zmq import ServerConnection
from domain import Angle, Direction, initial_input, Map, Material, Player, Position, Object
from use_case import move_player, rotate_player

def main(args):
  if args.connect:
    server = ServerConnection(args.connect, args.port)
    player = server.call("new_player")
    server.call("request_world_map")
    world_map = Map([], [], 0)
  else:
    server = None
    player = load_player_spawn(path='map')
    world_map = load_map(path='map')
  color_scheme = load_color_scheme(path='map')

  root = os.path.dirname(os.path.realpath(__file__))
  objects = load_images_for_enum(os.path.join(root, 'object'), Object)
  materials = load_images_for_enum(os.path.join(root, 'material'), Material)

  renderer = Renderer(
    window_size=(640, 480),
    materials=materials,
    objects=objects,
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
  running = True

  while running:
    if server:
      for event_name, data in server.poll_events():
        if event_name == "world_map":
          world_map = data
    last_time = time
    time = milliseconds_since_start()
    frame_time = min(time - last_time, max_frame_time) / 1000

    (input, running) = process_input(previous_input=input)
    player = rotate_player(player, input, frame_time, rotation_speed)
    player = move_player(player, world_map, input, frame_time, movement_speed)
    renderer.draw(color_scheme, world_map, player)

  return 0

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("--connect")
  parser.add_argument("--port", type=int, default=12345)
  args = parser.parse_args()
  sys.exit(main(args))
