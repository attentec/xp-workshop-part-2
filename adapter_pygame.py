import collections
import json
import math
import numpy
import os.path
import pygame

from domain import Direction, smallest_number, find_first_collision, Input, LineSegment, Map, Material, Object, Player, Position, SquareSide

pygame.init()

def _to_pygame_color(local_color):
  return pygame.Color(local_color.red, local_color.green, local_color.blue, local_color.alpha)

def _to_local_color(pygame_color):
  return Color(pygame_color.r, pygame_color.g, pygame_color.b, pygame_color.a)

def _color_tuple_from_json(string):
  return tuple(map(lambda s: int(s.strip()), string.lstrip('(').rstrip(')').split(',', maxsplit=2)))

def _color_from_json(string):
  color = _color_tuple_from_json(string)
  return Color(red=color[0], green=color[1], blue=color[2])

def _position_from_json(list):
  return Position(*map(float, list))

def _direction_from_json(list):
  return Direction(*map(float, list))

def _load_json_document(path):
  with open(path) as file:
    return json.load(file)

def _load_color_to_value_mapping(path, enum_class):
  document = _load_json_document(path)
  return { _color_tuple_from_json(color): enum_class(value) for color, value in document.items() }

def _load_map_layer(path, color_to_value):
  surface = pygame.image.load(path)
  width, height = surface.get_width(), surface.get_height()
  layer = [ None, ] * (width * height)

  for x in range(0, width):
    for y in range(0, height):
      color = surface.get_at((x, y))
      key = (int(color.r), int(color.g), int(color.b))
      layer[y*width + x] = color_to_value.get(key, None) if color.a > 0 else None

  return layer, width

def load_color_scheme(path):
  colors = _load_json_document(os.path.join(path, 'colors.json'))
  ceiling_color, floor_color = _color_from_json(colors['ceiling']), _color_from_json(colors['floor'])
  return ColorScheme(ceiling_color, floor_color)

def load_player_spawn(path):
  spawn = _load_json_document(os.path.join(path, 'spawn.json'))
  spawn_position, spawn_forward = _position_from_json(spawn['position']), _direction_from_json(spawn['forward'])
  return Player(spawn_position, spawn_forward)

def load_map(path):
  color_to_material = _load_color_to_value_mapping(os.path.join(path, 'materials.json'), Material)
  color_to_object = _load_color_to_value_mapping(os.path.join(path, 'objects.json'), Object)

  materials, width = _load_map_layer(os.path.join(path, 'materials.png'), color_to_material)
  objects, _ = _load_map_layer(os.path.join(path, 'objects.png'), color_to_object)

  return Map(materials, objects, width)

def process_input(previous_input):
  running = True
  pressed_keys = {}

  for event in pygame.event.get():
    if event.type == pygame.QUIT or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE):
      running = False
    elif event.type == pygame.KEYDOWN:
      pressed_keys[event.key] = True
    elif event.type == pygame.KEYUP:
      pressed_keys[event.key] = False

  input = Input(
    forward=pressed_keys.get(pygame.K_UP, previous_input.forward),
    backward=pressed_keys.get(pygame.K_DOWN, previous_input.backward),
    turn_left=pressed_keys.get(pygame.K_LEFT, previous_input.turn_left),
    turn_right=pressed_keys.get(pygame.K_RIGHT, previous_input.turn_right),
  )

  return (input, running)

def load_images_for_enum(directory, enum):
  images = {}

  for instance in enum:
    filename = '%s.png' % str(instance.name.lower())
    path = os.path.join(directory, filename)
    images[instance] = pygame.image.load(path)

  return images

_Size = collections.namedtuple('_Size', [ 'width', 'height', ])

class Color:
  def __init__(self, red, green, blue, alpha=255):
    self.red, self.green, self.blue, self.alpha = (red, green, blue, alpha)

  def __str__(self):
    return '(red=%d, green=%d, blue=%d, alpha=%d)' % (self.red, self.green, self.blue, self.alpha)

ColorScheme = collections.namedtuple('ColorScheme', [ 'ceiling', 'floor' ])

class _Camera:
  def __init__(self, player, size, field_of_view):
    self.position = player.position
    self.__fov_scale = math.tan(field_of_view.to_radians() / 2)
    self.__aspect_ratio = size.width / (size.height + smallest_number)
    self.__width = size.width
    self.forward = player.forward.normalize()
    self.__right = Direction(-self.forward.y, self.forward.x)

  def direction_for_column(self, column):
    normalized_x = self.__convert_column_to_normalized_coordinate(column)
    right_scale = self.__fov_scale * self.__aspect_ratio * normalized_x
    direction = self.forward + self.__right*right_scale
    return direction.normalize()

  def column_for_direction(self, direction_in_view_coordinates):
    direction = direction_in_view_coordinates.normalize()
    right_scale = direction.x / (direction.y + smallest_number)
    normalized_x = right_scale / (self.__fov_scale * self.__aspect_ratio + smallest_number)
    return self.__convert_normalized_coordinate_to_column(normalized_x)

  def __convert_column_to_normalized_coordinate(self, column):
    return (2*column) / (self.__width + smallest_number) - 1

  def __convert_normalized_coordinate_to_column(self, coordinate):
    return int((self.__width * (coordinate + 1)) / 2)

  def to_view_position(self, position):
    delta = position - self.position
    return Position(self.__right.dot(delta), self.forward.dot(delta))

def _darken_surface(surface, scale):
  copy = surface.copy()
  int_scale = int(255 * scale)
  surface.fill((int_scale, int_scale, int_scale, int_scale), rect=None, special_flags=pygame.BLEND_RGBA_MULT)
  return surface

class Renderer:
  def __init__(self, window_size, materials, objects, field_of_view, draw_distance, far_color, shade_scale, object_scale):
    self.__screen = pygame.display.set_mode(window_size)
    self.__size = _Size(self.__screen.get_width(), self.__screen.get_height())
    self.__buffer = numpy.zeros(window_size, dtype=numpy.uint32)
    self.__field_of_view, self.__draw_distance = field_of_view, draw_distance
    self.__far_color, self.__shade_scale = self.__screen.map_rgb(_to_pygame_color(far_color)), shade_scale
    self.__object_scale = object_scale
    self.__z_buffer = numpy.zeros((self.__size.width, ), dtype='float32')

    self.__materials = { material: self.__convert_texture_to_array(texture) for material, texture in materials.items() }
    self.__shaded_materials = { material: self.__convert_texture_to_array(_darken_surface(texture, shade_scale)) for material, texture in materials.items() }
    self.__objects = objects

  def __convert_texture_to_array(self, texture):
    texture_in_screen_color_space = texture.convert()
    mapped_colors = pygame.surfarray.array2d(texture_in_screen_color_space)
    transposed = mapped_colors.T
    return transposed

  def draw(self, color_scheme, world_map, player):
    half_height = int(self.__size.height / 2)
    self.__buffer[:, :half_height] = self.__screen.map_rgb(_to_pygame_color(color_scheme.ceiling))
    self.__buffer[:, half_height:] = self.__screen.map_rgb(_to_pygame_color(color_scheme.floor))
    self.__z_buffer.fill(self.__draw_distance)

    camera = _Camera(player, self.__size, self.__field_of_view)

    for x in range(0, self.__size.width):
      direction = camera.direction_for_column(x)
      line_segment = LineSegment(start=camera.position, end=camera.position+direction*self.__draw_distance)
      collision = find_first_collision(world_map, line_segment)

      if collision is None:
        (start, end) =  self.__get_vertical_span(self.__draw_distance)
        self.__buffer[x, start:end] = self.__far_color
      else:
        fish_eye_corrected_distance = collision.distance * direction.dot(camera.forward)
        (start, end) = self.__get_vertical_span(fish_eye_corrected_distance)

        material = world_map.material(collision.position)
        use_shade = collision.side != SquareSide.HORIZONTAL
        flip_texture = collision.side == SquareSide.HORIZONTAL and direction.x < 0 or \
          collision.side == SquareSide.VERTICAL and direction.y > 0
        wall_x = collision.wall

        if collision.distance < self.__z_buffer[x]:
          column = pygame.Rect(x, start, 1, end-start+1)
          self.__draw_column(column, material, use_shade, flip_texture, wall_x)
          self.__z_buffer[x] = collision.distance

    pygame.surfarray.blit_array(self.__screen, self.__buffer)

    for (object, position) in world_map.all_objects():
      self.__draw_object(object, position, camera)

    pygame.display.flip()

  def __get_vertical_span(self, distance, scale=1):
    center_y = self.__size.height / 2

    line_height = scale * self.__size.height / (distance + smallest_number)
    half_line_height = line_height / 2

    start = max(0, int(center_y - half_line_height))
    end = min(int(center_y + half_line_height), self.__size.height - 1)

    return (start, end)

  def __draw_column(self, rectangle, material, use_shade, flip_texture, wall_x):
    x, y_start, height = rectangle.x, rectangle.y, rectangle.height
    y_end = y_start + rectangle.height

    materials = self.__shaded_materials if use_shade else self.__materials
    texture = materials[material]
    texture_width, texture_height = texture.shape

    normalized_x = wall_x - math.floor(wall_x)
    texture_x = max(0, min( texture_width-1, int(normalized_x * texture_width)))

    if flip_texture:
      texture_x = texture_width-1 - texture_x

    indices = numpy.linspace(0, texture_height-1, num=height, dtype=numpy.uint32)
    self.__buffer[x,y_start:y_end] = texture[indices,texture_x]

  def __draw_object(self, object, position, camera):
    view_position = camera.to_view_position(position)
    distance = view_position.length()
    is_behind_camera = view_position.y < 0

    if is_behind_camera or distance > self.__draw_distance:
      return

    (y_start, y_end) = self.__get_vertical_span(distance, scale=self.__object_scale)
    height = y_end - y_start
    width = height

    center_x = camera.column_for_direction(view_position)
    half_width = int(width / 2)
    original_start = center_x - half_width

    x_start = max(0, min(self.__size.width - 1, original_start))
    x_end = max(0, min(self.__size.width - 1, center_x + half_width))
    x_offset = abs(original_start - x_start)

    if x_start == x_end or y_start == y_end:
      return

    texture = self.__objects[object]
    scaled_texture = pygame.transform.scale(texture, (width, height))

    for i in range(x_end - x_start):
      x = x_start + i

      if distance < self.__z_buffer[x]:
        self.__screen.blit(scaled_texture, (x, y_start), pygame.Rect(x_offset + i, 0, 1, height))
        self.__z_buffer[x] = distance

def milliseconds_since_start():
  return pygame.time.get_ticks()
