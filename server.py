import sys

from adapter_pygame import load_map
from adapter_zmq import Server
from domain import Color, Direction, Player, Position

def main(args):
  server = Server(12345)
  world_map = load_map(
    path='world.png',
    ceiling_color=Color(red=0x33, green=0x33, blue=0x33),
    floor_color=Color(red=0x55, green=0x55, blue=0x55)
  )
  player_start = Player(
    position=Position(x=22.5, y=13.5), # TODO: Find player start with a special color?
    forward=Direction(x=-1, y=0)
  )
  handler = Handler(world_map, player_start)
  while True:
    server.serve(handler)

class Handler:
  def __init__(self, world_map, player_start):
    self.__world_map = world_map
    self.__player_start = player_start

  def handle_new_player_command(self, _):
    return self.__player_start

  def handle_get_map_command(self, _):
    return self.__world_map

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
