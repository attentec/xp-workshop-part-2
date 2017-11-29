import argparse
import sys

from adapter_pygame import load_links, load_map, load_player_spawn
from adapter_zmq import Server
from server_use_case import handle_command, initial_state

def main(args):
  server = Server(args.port)
  player_spawn = load_player_spawn(path='map')
  world_map = load_map(path='map')
  links = load_links(path='map')

  state = initial_state(player_spawn, world_map, links)

  def command_fn(command_name, input_data):
    nonlocal state
    next_state, output_data, events = handle_command(state, command_name, input_data)
    for event_name, event_data in events:
      server.emit_event(event_name, event_data)
    state = next_state
    return output_data

  server.serve(command_fn)

  return 0

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("--port", type=int, default=12345)
  args = parser.parse_args()
  sys.exit(main(args))
