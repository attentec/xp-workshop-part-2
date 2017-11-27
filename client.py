import os.path
import sys

from adapter_pygame import milliseconds_since_start, load_map, load_textures, process_input, Renderer
from adapter_zmq import ServerConnection
from domain import Angle, Color, Direction, Input, Player, Position
from use_case import move_player, rotate_player

def main(args):
  server = ServerConnection("localhost", 12345)
  player = server.request("new_player")
  world_map = server.request("get_map")

  root = os.path.dirname(os.path.realpath(__file__))
  textures = load_textures(os.path.join(root, 'textures'))

  renderer = Renderer(
    window_size=(640, 480),
    textures=textures,
    field_of_view=Angle.from_degrees(66),
    draw_distance=100,
    far_color=Color(red=0, green=0, blue=0),
    shade_scale=0.85
  )
  input = Input(
    forward=False,
    backward=False,
    turn_left=False,
    turn_right=False
  )

  max_frame_time = 50
  rotation_speed = 3
  movement_speed = 5

  time = milliseconds_since_start()
  running = True

  while running:
    last_time = time
    time = milliseconds_since_start()
    frame_time = min(time - last_time, max_frame_time) / 1000

    (input, running) = process_input(previous_input=input)
    player = rotate_player(player, input, frame_time, rotation_speed)
    player = move_player(player, world_map, input, frame_time, movement_speed)
    renderer.draw(world_map, player)

  return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
