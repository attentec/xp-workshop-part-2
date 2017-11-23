import math
import pygame
import sys

class Vector:
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def rotate(self, angle):
    return Vector(
      self.x * math.cos(angle) - self.y * math.sin(angle),
      self.x * math.sin(angle) + self.y * math.cos(angle)
    )

class Player:
  def __init__(self):
    self.position = Vector(22, 13)
    self.direction = Vector(-1, 0)
    self.plane = Vector(0, 0.66)

  def update(self, world_map, frame_time, keys_down):
    move_speed = frame_time * 5
    rotation_speed = frame_time * 3

    x = 0
    y = 0

    if keys_down & KEY_UP:
      x = int(self.position.x + self.direction.x * move_speed)
      y = int(self.position.y)

      if world_map.is_empty(x, y): # TODO: Check first intersection instead (can walk through corners now)
        self.position.x += self.direction.x * move_speed

      x = int(self.position.x)
      y = int(self.position.y + self.direction.y * move_speed)

      if world_map.is_empty(x, y):
        self.position.y += self.direction.y * move_speed

    if keys_down & KEY_DOWN:
      x = int(self.position.x - self.direction.x * move_speed)
      y = int(self.position.y)

      if world_map.is_empty(x, y):
        self.position.x -= self.direction.x * move_speed

      x = int(self.position.x)
      y = int(self.position.y - self.direction.y * move_speed)

      if world_map.is_empty(x, y):
        self.position.y -= self.direction.y * move_speed

    if keys_down & KEY_RIGHT:
      self.direction = self.direction.rotate(-rotation_speed)
      self.plane = self.plane.rotate(-rotation_speed)

    if keys_down & KEY_LEFT:
      self.direction = self.direction.rotate(rotation_speed)
      self.plane = self.plane.rotate(rotation_speed)

class Map:
  def __init__(self, surface):
    self.__surface = surface

  def is_empty(self, x, y):
    return self.color(x, y).a == 0

  def color(self, x, y):
    return self.__surface.get_at((x, y))

def load_map(path):
  return Map(pygame.image.load(path))

epsilon = sys.float_info.epsilon

KEY_UP = 0x000100
KEY_DOWN = 0x001000
KEY_RIGHT = 0x000010
KEY_LEFT = 0x000001

ceiling_color = pygame.Color(0x33, 0x33, 0x33)
floor_color = pygame.Color(0x55, 0x55, 0x55)

screen_width = 640
screen_height = 480

def draw_vertical_line(screen, x, start_y, end_y, color):
  if end_y < start_y:
    temp = start_y
    start_y = end_y
    end_y = temp

  if (end_y < 0) or (start_y >= screen_height) or (x < 0) or (x >= screen_width):
    return

  if start_y < 0:
    start_y = 0

  if end_y >= screen_height:
    end_y = screen_height - 1

  destination = pygame.Rect(x, start_y, 1, end_y - start_y + 1)
  screen.fill(color, destination)

def draw_world(screen, world_map, player):
  width = screen_width
  height = screen_height

  for x in range(0, width):
    cameraX = ((2 * x) / width) - 1

    ray_position = Vector(player.position.x, player.position.y)
    ray_direction = Vector(player.direction.x + player.plane.x * cameraX, player.direction.y + player.plane.y * cameraX)

    mapX = int(ray_position.x)
    mapY = int(ray_position.y)

    side_distance = Vector(0, 0)
    squared_ray_direction = Vector(ray_direction.x * ray_direction.x, ray_direction.y * ray_direction.y)
    delta_distance = Vector(math.sqrt(1 + squared_ray_direction.y / (squared_ray_direction.x + epsilon)), math.sqrt(1 + squared_ray_direction.x / (squared_ray_direction.y + epsilon)))

    step_x = 0
    step_y = 0

    if ray_direction.x < 0:
      step_x = -1
      side_distance.x = (ray_position.x - mapX) * delta_distance.x
    else:
      step_x = 1
      side_distance.x = (mapX + 1 - ray_position.x) * delta_distance.x

    if ray_direction.y < 0:
      step_y = -1
      side_distance.y = (ray_position.y - mapY) * delta_distance.y
    else:
      step_y = 1
      side_distance.y = (mapY + 1 - ray_position.y) * delta_distance.y

    hit = False
    side = 0

    while not hit:
      if side_distance.x < side_distance.y:
        side_distance.x += delta_distance.x
        mapX += step_x
        side = 0
      else:
        side_distance.y += delta_distance.y
        mapY += step_y
        side = 1

      if not world_map.is_empty(mapX, mapY):
        hit = True

    if side == 0:
      perpendicular_wall_distance = abs((mapX - ray_position.x + (1 - step_x) / 2) / ray_direction.x)
    else:
      perpendicular_wall_distance = abs((mapY - ray_position.y + (1 - step_y) / 2) / ray_direction.y)

    line_height = abs(int(height / (perpendicular_wall_distance + epsilon)))
    start_y = max(0, (-line_height / 2) + (height / 2))
    end_y = min((line_height / 2) + (height / 2), height - 1)
    color = world_map.color(mapX, mapY)

    if side == 1:
      color = pygame.Color(int(color.r / 2), int(color.g / 2), int(color.b / 2))

    draw_vertical_line(screen, x, start_y, end_y, color)

def process_events(keys_down):
  result = True

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      result = False
    elif event.type == pygame.KEYDOWN:
      if event.key == pygame.K_UP:
        keys_down |= KEY_UP
      elif event.key == pygame.K_DOWN:
        keys_down |= KEY_DOWN
      elif event.key == pygame.K_RIGHT:
        keys_down |= KEY_RIGHT
      elif event.key == pygame.K_LEFT:
        keys_down |= KEY_LEFT
    elif event.type == pygame.KEYUP:
      if event.key == pygame.K_UP:
        keys_down &= ~KEY_UP
      elif event.key == pygame.K_DOWN:
        keys_down &= ~KEY_DOWN
      elif event.key == pygame.K_RIGHT:
        keys_down &= ~KEY_RIGHT
      elif event.key == pygame.K_LEFT:
        keys_down &= ~KEY_LEFT
      elif event.key == pygame.K_ESCAPE:
        result = False

  return (result, keys_down)

def main(args):
  pygame.init()
  screen = pygame.display.set_mode((screen_width, screen_height))

  world_map = load_map('world.png')
  player = Player()

  running = True
  keys_down = 0
  time = 0

  while running:
    (running, keys_down) = process_events(keys_down)

    screen.fill(ceiling_color, pygame.Rect(0, 0, screen_width, screen_height / 2))
    screen.fill(floor_color, pygame.Rect(0, (screen_height / 2) + 1, screen_width, screen_height / 2))

    old_time = time
    time = pygame.time.get_ticks()
    frame_time = (time - old_time) / 1000

    draw_world(screen, world_map, player)
    player.update(world_map, frame_time, keys_down)

    pygame.display.flip()
    pygame.time.wait(5)

  return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
