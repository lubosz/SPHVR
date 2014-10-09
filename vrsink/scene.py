__author__ = 'Lubosz Sarnecki'

from gi.repository import Graphene, Gdk
import numpy
import math
from vrsink.graphics import *
from numpy import array


def matrix_to_array(m):
    result = []
    for x in range(0, 4):
        result.append([m.get_value(x, 0),
                       m.get_value(x, 1),
                       m.get_value(x, 2),
                       m.get_value(x, 3)])
    return numpy.array(result, 'd')


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

    def draw(self, sink, context, video_texture, w, h):
        if not self.init:
            return

        context.clear_shader()

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        context.clear_shader()
        self.graphics["video"].draw(video_texture, matrix_to_array(self.zoom_matrix))
        context.clear_shader()

        return True

