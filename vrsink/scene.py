__author__ = 'Lubosz Sarnecki'

from gi.repository import Graphene, Gdk
import numpy
import math
from vrsink.graphics import *
from numpy import array
from numpy import identity, dot


def matrix_to_array(m):
    result = []
    for x in range(0, 4):
        result.append([m.get_value(x, 0),
                       m.get_value(x, 1),
                       m.get_value(x, 2),
                       m.get_value(x, 3)])
    return numpy.array(result, 'd')

def print_matrix(m):
  if type(m) == Graphene.Matrix:
    for x in range(0, 4):
      print("%.3f %.3f %.3f %.3f" % (m.get_value(x, 0),
        m.get_value(x, 1),
        m.get_value(x, 2),
        m.get_value(x, 3)))
  else:
    for i in range(0, 4):
      print("%.3f %.3f %.3f %.3f" % (m.column(i).x(),
        m.column(i).y(),
        m.column(i).z(),
        m.column(i).w()))
  print()

class Scene():
    def __init__(self):
        self.handles = {}
        self.graphics = {}
        self.width, self.height = 0, 0
        self.init = False
        self.window = None

    def relative_position(self, event):
        # between 0 and 1
        x = event.x / self.width
        y = 1.0 - (event.y / self.height)

        # between -1 and 1
        return (2 * x - 1,
                (2 * y - 1))

    def aspect(self):
        if self.width == 0 or self.height == 0:
            return 1
        return self.width / self.height

    def set_cursor(self, type):
        display = Gdk.Display.get_default()
        cursor = Gdk.Cursor.new_for_display(display, type)
        self.window.get_window().set_cursor(cursor)

    def reshape(self, sink, context, width, height):
        self.width, self.height = width, height
        if not self.init:
            self.init_gl(context)
            self.init = True
        glViewport(0, 0, width, height)
        return True

    def init_gl(self, context):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_RECTANGLE)


class VRScene(Scene):
    def __init__(self):
        Scene.__init__(self)

        self.graphics["video"] = VideoGraphic()

        self.selected = False
        self.slider_box = None
        self.action = None

        self.zoom = 1.0
        self.set_zoom_matrix(self.zoom)
        self.init_projection()

    def set_zoom_matrix(self, zoom):
        self.zoom_matrix = Graphene.Matrix.alloc()
        self.zoom_matrix.init_scale(zoom, zoom, 1.0)

    def set_zoom(self, scale):
        self.zoom = scale.get_value()
        self.set_zoom_matrix(self.zoom)

    def init_gl(self, context):
        Scene.init_gl(self, context)

        self.graphics["video"].init_gl(context)

        self.init = True

    def get_projection(self):
        projection = Graphene.Matrix()
        projection.init_perspective(90.0, 4.0/3.0, 0.01, 100.0)
        return matrix_to_array(projection)

    def get_view(self):
        eye = Graphene.Vec3()
        center = Graphene.Vec3()
        up = Graphene.Vec3()
        eye.init(0, 0, 5)
        center.init(0, 0, 0)
        up.init(0, 1, 0)

        view = Graphene.Matrix()
        view.init_look_at(eye, center, up)
        return matrix_to_array(view)

    def init_projection(self):
        #model = identity(4)

        projection = self.get_projection()
        view = self.get_view()
        #vp = matrix_to_array(projection) * matrix_to_array(view)
        #vp = np_projection * np_view
        vp = dot(view, projection)
        self.mvp = vp
        #self.mvp = dot(model, vp)
        #self.mvp = np_view
        #print(self.mvp)

    def draw(self, sink, context, video_texture, w, h):
        if not self.init:
            return

        context.clear_shader()

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        context.clear_shader()
        self.graphics["video"].draw(video_texture, self.mvp)
        context.clear_shader()

        return True

