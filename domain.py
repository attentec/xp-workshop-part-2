import collections
import enum
import math
import sys

smallest_number = sys.float_info.epsilon

class Angle:
  def __init__(self, radians):
    self.__radians = radians

  @classmethod
  def from_radians(class_, radians):
    return class_(radians)

  @classmethod
  def from_degrees(class_, degrees):
    return class_((math.pi * degrees) / 180)

  def to_radians(self):
    return self.__radians

  def to_degrees(self):
    return (180 * self.__radians) / math.pi

class Color:
  def __init__(self, red, green, blue, alpha=255):
    self.red, self.green, self.blue, self.alpha = (red, green, blue, alpha)

  def __str__(self):
    return '(red=%d, green=%d, blue=%d, alpha=%d)' % (self.red, self.green, self.blue, self.alpha)

class _Vector:
  def __init__(self, x, y):
    self.x, self.y = x, y

  def __str__(self):
    return '(x=%f, y=%f)' % (self.x, self.y)

  def __add__(self, v):
    return _Vector(self.x + v.x, self.y + v.y)

  def __sub__(self, v):
    return _Vector(self.x - v.x, self.y - v.y)

  def __mul__(self, s):
    return _Vector(self.x * s, self.y * s)

  def __div__(self, s):
    return _Vector(self.x / s, self.y / s)

  def length(self):
    return math.sqrt(self.x*self.x + self.y*self.y)

  def normalize(self):
    return self * (1 / (self.length() + smallest_number))

  def abs(self):
    return _Vector(abs(self.x), abs(self.y))

  def to_grid(self):
    return _Vector(int(math.floor(self.x)), int(math.floor(self.y)))

  def dot(self, v):
    return self.x*v.x + self.y*v.y

  def rotate(self, angle):
    radians = angle.to_radians()
    x = self.x * math.cos(radians) - self.y * math.sin(radians)
    y = self.x * math.sin(radians) + self.y * math.cos(radians)
    return _Vector(x, y)

Direction = _Vector
Position = _Vector

LineSegment = collections.namedtuple('LineSegment', [ 'start', 'end', ])
Input = collections.namedtuple('Input', [ 'forward', 'backward', 'turn_left', 'turn_right', ])
Player = collections.namedtuple('Player', [ 'position', 'forward', ])

@enum.unique
class Material(enum.Enum):
  VOID = 0
  DUMMY = 1

@enum.unique
class Object(enum.Enum):
  KEY = 0

class Map:
  def __init__(self, ceiling_color, floor_color, materials, objects, width):
    self.ceiling_color, self.floor_color = ceiling_color, floor_color
    self.__outside_color = Color(0, 0, 0)
    self.__materials, self.__objects, self.__width = materials, objects, width

  def __to_index(self, position):
    grid_position = position.to_grid()
    return grid_position.y*self.__width + grid_position.x

  def material(self, position):
    index = self.__to_index(position)
    return self.__materials[index] if index >= 0 and index < len(self.__materials) else Material.VOID

  def object(self, position):
    index = self.__to_index(position)
    return self.__objects[index] if index >= 0 and index < len(self.__objects) else None

class SquareSide(enum.Enum):
  HORIZONTAL = 0
  VERTICAL = 1

Collision = collections.namedtuple('Collision', [ 'position', 'distance', 'wall', 'side', ])

def find_first_collision(map, line_segment, debug=False):
  start, end = line_segment.start, line_segment.end
  grid_start, grid_end = start.to_grid(), end.to_grid()
  delta = end - start

  if abs(delta.x) < smallest_number and abs(delta.y) < smallest_number:
    return None

  direction = delta.normalize()
  dy_dx = math.inf if abs(direction.x) < smallest_number else direction.y / direction.x
  dx_dy = math.inf if abs(direction.y) < smallest_number else direction.x / direction.y

  horizontal_crossing_distance = math.sqrt(1 + dy_dx*dy_dx)
  vertical_crossing_distance = math.sqrt(1 + dx_dy*dx_dy)

  if abs(direction.x) < smallest_number:
    step_x = 0
    next_horizontal_crossing = math.inf
  elif direction.x < 0:
    step_x = -1
    next_horizontal_crossing = horizontal_crossing_distance * (start.x - grid_start.x)
  else:
    step_x = 1
    next_horizontal_crossing = horizontal_crossing_distance * (grid_start.x + 1 - start.x)

  if abs(direction.y) < smallest_number:
    step_y = 0
    next_vertical_crossing = math.inf
  elif direction.y < 0:
    step_y = -1
    next_vertical_crossing = vertical_crossing_distance * (start.y - grid_start.y)
  else:
    step_y = 1
    next_vertical_crossing = vertical_crossing_distance * (grid_start.y + 1 - start.y)

  steps = abs(grid_end.x - grid_start.x) + abs(grid_end.y - grid_start.y)
  x, y = grid_start.x, grid_start.y

  for _ in range(steps):
    if next_horizontal_crossing < next_vertical_crossing:
      side = SquareSide.HORIZONTAL
      next_horizontal_crossing += horizontal_crossing_distance
      x += step_x
    else:
      side = SquareSide.VERTICAL
      next_vertical_crossing += vertical_crossing_distance
      y += step_y

    position = Position(x, y)

    if map.material(position) is not None:
      if side == SquareSide.HORIZONTAL:
        distance = abs((x - start.x + (1 - step_x) / 2) / direction.x)
        wall = start.y + distance * direction.y
      else:
        distance = abs((y - start.y + (1 - step_y) / 2) / direction.y)
        wall = start.x + distance * direction.x

      return Collision(position, distance, wall, side)

  return None
