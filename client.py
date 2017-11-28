import os.path
import sys

from adapter_pygame import Color, milliseconds_since_start, load_map, load_images_for_enum, process_input, Renderer
from domain import Angle, Direction, Input, Material, Player, Position, Object
from use_case import move_player, rotate_player

def main(args):
  world_map = load_map(path='map')
  player = Player(position=world_map.spawn_position, forward=world_map.spawn_forward)

  root = os.path.dirname(os.path.realpath(__file__))
  objects = load_images_for_enum(os.path.join(root, 'objects'), Object)
  materials = load_images_for_enum(os.path.join(root, 'materials'), Material)

  renderer = Renderer(
    window_size=(640, 480),
    materials=materials,
    objects=objects,
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
