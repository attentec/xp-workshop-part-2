from use_case import *
from domain import Direction, initial_input, Map, Material, Position

MAP = Map(materials=[Material.FLOOR, Material.FLOOR, Material.FLOOR,
                     Material.FLOOR, Material.FLOOR, Material.FLOOR,
                     Material.FLOOR, Material.FLOOR, Material.FLOOR],
          objects=[],
          width=3)
PLAYER = Player(name='test',
                position=Position(1.5, 1.5),
                forward=Direction(0.0, -1.0))

def test_move_forward():
  state = initial_state(initial_input, PLAYER, MAP, 3, 5)
  state, _ = handle_event(state, 'input', initial_input._replace(forward=True))
  state, _ = handle_event(state, 'tick', 0.070)
  assert state.player.position.x == 1.5
  assert state.player.position.y < 1.5
  assert state.player.forward.x == 0.0
  assert state.player.forward.y == -1.0

def test_turn_right():
  state = initial_state(initial_input, PLAYER, MAP, 3, 5)
  state, _ = handle_event(state, 'input', initial_input._replace(turn_right=True))
  state, _ = handle_event(state, 'tick', 0.070)
  assert state.player.position.x == 1.5
  assert state.player.position.y == 1.5
  assert state.player.forward.x > 0.0
  assert state.player.forward.y > -1.0
