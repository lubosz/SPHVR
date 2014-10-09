from gi.repository import Clutter
import cairo
import numpy
from math import pi

from OpenGL.GL import *
from vrsink.opengl import *


class Graphic():
    def __init__(self):
        self.texture = None
        self.texture_clicked = None
        self.shader = None
        self.mesh = None


class VideoGraphic(Graphic):
    def __init__(self):
        Graphic.__init__(self)

    def init_gl(self, context):
        #self.shader = Shader(context, "simple.vert", "video.frag")
        #self.mesh = PlaneTriangleFan()

        self.shader = Shader(context, "no-uv.vert", "color.frag")
        self.mesh = SphereTriangleStrip()

    def draw(self, video_texture, matrix):
        self.shader.use()
        self.mesh.bind(self.shader)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, video_texture)
        self.shader.shader.set_uniform_1i("videoSampler", 0)

        self.shader.set_matrix("mvp", matrix)

        self.mesh.draw()
        self.mesh.unbind()