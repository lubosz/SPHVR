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


class HandleActor():
    def __init__(self, drag, x=0, y=0):
        self.position = (x, y)
        self.clicked = False
        self.initital_position = self.position
        self.drag = drag
        self.size = 1.0

    def is_clicked(self, click):
        vclick = Graphene.Vec2.alloc()
        vclick.init(click[0], click[1])
        vpos = Graphene.Vec2.alloc()
        vpos.init(self.position[0], self.position[1])
        vdistance = vclick.subtract(vpos)

        hovered = vdistance.length() < 0.05 * self.size

        self.hovered = hovered

        return hovered

    def reposition(self, matrix, aspect):
            vector = numpy.array([self.initital_position[0] * aspect,
                                  self.initital_position[1], 0, 1])
            vector_transformed = numpy.dot(vector, matrix)

            self.position = (vector_transformed[0], -vector_transformed[1])

    def distance_to(self, actor):
        distance = array(self.position) - array(actor.position)
        return numpy.sqrt(distance.dot(distance))

    def model_matrix(self):
        model_matrix = Graphene.Matrix.alloc()

        model_matrix.init_scale(self.size, self.size, 1.0)

        translation_vector = Graphene.Point3D.alloc()
        translation_vector.init(self.position[0], self.position[1], 0)

        model_matrix.translate(translation_vector)

        return matrix_to_array(model_matrix)


class VRScene(Scene):
    def __init__(self):
        Scene.__init__(self)

        self.corner_handles = {
            "1BL": HandleActor(self.scale_keep_aspect, -1, -1),
            "2TL": HandleActor(self.scale_keep_aspect, -1, 1),
            "3TR": HandleActor(self.scale_keep_aspect, 1, 1),
            "4BR": HandleActor(self.scale_keep_aspect, 1, -1)}

        self.edge_handles = {
            "left": HandleActor(self.scale_height, -1, 0),
            "right": HandleActor(self.scale_height, 1, 0),
            "top": HandleActor(self.scale_width, 0, 1),
            "bottom": HandleActor(self.scale_width, 0, -1)}

        self.graphics["handle"] = HandleGraphic(100, 100)
        self.graphics["video"] = VideoGraphic()
        self.graphics["box"] = BoxGraphic(self.corner_handles.values())

        self.graphics["background"] = BackgroundGraphic()

        self.handles = list(self.corner_handles.values()) \
                       + list(self.edge_handles.values())

        #self.box_actor = BoxActor(self.translate)
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

        cairo_shader = Shader(context, "simple.vert", "cairo.frag")

        self.graphics["handle"].init_gl(
            context, self.width, self.height, cairo_shader)
        self.graphics["box"].init_gl(
            context, self.width, self.height, cairo_shader)
        self.graphics["video"].init_gl(context)
        self.graphics["background"].init_gl(
            context, self.width, self.height, cairo_shader)

        self.init = True

    def draw(self, sink, context, video_texture, w, h):
        if not self.init:
            return

        context.clear_shader()

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        context.clear_shader()
        self.graphics["background"].draw()
        context.clear_shader()
        self.graphics["video"].draw(video_texture, matrix_to_array(self.zoom_matrix))
        context.clear_shader()

        return True

    def scale_width(self, event):
        scale_y = self.slider_box.sliders["scale-y"]
        scale_y.set(self.center_distance(event))

    def scale_height(self, event):
        scale_x = self.slider_box.sliders["scale-x"]
        scale_x.set(self.center_distance(event))

    def center_distance(self, event):
        center = self.box_actor.get_center(self.corner_handles)
        distance = center - array(self.relative_position(event))
        return numpy.sqrt(distance.dot(distance)) / self.zoom

    def scale_keep_aspect(self, event):
        old_aspect = self.old_scale[0] / self.old_scale[1]
        scale_x = self.slider_box.sliders["scale-x"]
        scale_y = self.slider_box.sliders["scale-y"]
        distance = self.center_distance(event)
        scale_x.set(old_aspect * distance / math.sqrt(2))
        scale_y.set(distance / math.sqrt(2))