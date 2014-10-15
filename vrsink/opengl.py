__author__ = 'Lubosz Sarnecki'

from OpenGL.GL import *
from gi.repository import GstGL
import cairo
from numpy import array

class Mesh():
    def __init__(self, type):
        self.type = type
        self.buffers = {}
        self.locations = {}
        self.element_sizes = {}

    def add(self, name, buffer, element_size):
        self.buffers[name] = buffer
        self.element_sizes[name] = element_size

    def set_index(self, index):
        self.index = index

    def bind(self, shader):
        for name in self.buffers:
            self.locations[name] = shader.shader.get_attribute_location(name)
            glVertexAttribPointer(
                self.locations[name],
                self.element_sizes[name],
                GL_FLOAT, GL_FALSE, 0,
                self.buffers[name])
            glEnableVertexAttribArray(self.locations[name])

    def draw(self):
        glDrawElements(self.type,
                       1024*11,
                       GL_UNSIGNED_SHORT,
                       self.index)

    def unbind(self):
        for name in self.buffers:
            glDisableVertexAttribArray(self.locations[name])


class SphereTriangleStrip(Mesh):
    def __init__(self):
        #Mesh.__init__(self, GL_TRIANGLE_STRIP)
        Mesh.__init__(self, GL_TRIANGLES)

        stacks = 32
        slices = 32
        width = 1.0
        height = 1.0
        depth = 1.0
        radius = 1.0
        distance = 3.0

        center = array([0, 0, 0])

        positions = []
        #thepos = array([])

        from math import pi, sin, cos
        from numpy import concatenate, add
        from IPython import embed


        #LEFT
        for stack in range(0, stacks):
            phi = pi / 2.0 - stack * pi / stacks
            y = radius * sin(phi) * height
            scale = -radius * cos(phi)

            for slice in range(0, slices):
                theta = slice * 2.0 * pi / slices
                x = scale * sin(theta) * width + radius
                z = scale * cos(theta) * depth

                normal = array([x + distance, y, z])
                positions += list(normal + center)

        #RIGHT
        for stack in range(0, stacks):
            phi = pi / 2.0 - stack * pi / stacks
            y = radius * sin(phi) * height
            scale = -radius * cos(phi)

            for slice in range(0, slices):
                theta = slice * 2.0 * pi / slices
                x = scale * sin(theta) * width - radius
                z = scale * cos(theta) * depth

                normal = array([x - distance, y, z])
                positions += list(normal + center)

        self.add("position", positions, 3)
        #self.add("uv", positions, 2)

        indices = []

        for foo in range(0, int(len(positions) / 3)):
            indices.append(foo)

        #self.set_index(indices)


        triangle_indices = []

        # LEFT
        for stack in range(0, stacks):
            top = (stack + 0) * (slices + 1)
            bot = (stack + 1) * (slices + 1)

            for slice in range(0, slices):
                if stack != 0:
                    triangle_indices.append(top + slice)
                    triangle_indices.append(bot + slice)
                    triangle_indices.append(top + slice + 1)

                if stack != stacks - 1:
                    triangle_indices.append(top + slice + 1)
                    triangle_indices.append(bot + slice)
                    triangle_indices.append(bot + slice + 1)


        # RIGHT
        for stack in range(stacks, stacks * 2 - 1):
            top = (stack + 0) * (slices + 1)
            bot = (stack + 1) * (slices + 1)

            for slice in range(0, slices):
                if stack != 0:
                    triangle_indices.append(top + slice)
                    triangle_indices.append(bot + slice)
                    triangle_indices.append(top + slice + 1)

                if stack != stacks - 1:
                    triangle_indices.append(top + slice + 1)
                    triangle_indices.append(bot + slice)
                    triangle_indices.append(bot + slice + 1)

        #print(len(triangle_indices))
        #print(len(indices))
        #print(len(positions) / 3)



        #glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        #glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        #self.set_index(indices)

        # over / under uvs
        textureCoordinates = []

        #LEFT

        for stack in range(0, stacks):
            for slice in reversed(range(0, slices)):
                textureCoordinates.append(slice / slices)
                textureCoordinates.append(stack / stacks / 2)

        # RIGHT
        for stack in range(0, stacks):
            for slice in reversed(range(0, slices)):
                textureCoordinates.append(slice / slices)
                textureCoordinates.append(0.5 + stack / stacks / 2)

        self.add("uv", textureCoordinates, 2)

        print("textureCoordinates/2", len(textureCoordinates)/2)
        print("triangle_indices", len(triangle_indices))
        print("positions/3", len(positions)/3)



        self.set_index(triangle_indices)



class PlaneTriangleFan(Mesh):
    def __init__(self):
        Mesh.__init__(self, GL_TRIANGLE_STRIP)
        #Mesh.__init__(self, GL_LINES)
        self.add(
            "position", [
                -1, 1, 0, 1,
                1, 1, 0, 1,
                1, -1, 0, 1,
                -1, -1, 0, 1], 4)

        self.add(
            "uv", [
                0.0, 0.0,
                1.0, 0.0,
                1.0, 1.0,
                0.0, 1.0], 2)

        self.set_index([0, 1, 3, 2])


class PlaneCairo(Mesh):
    def __init__(self, canvas_width, canvas_height, object_width, object_height):
        Mesh.__init__(self, GL_TRIANGLE_STRIP)

        w, h = object_width / canvas_width, \
               object_height / canvas_height

        self.add(
            "position", [
                -w, h, 0, 1,
                w, h, 0, 1,
                w, -h, 0, 1,
                -w, -h, 0, 1], 4)

        self.add(
            "uv", [
                0.0, 0.0,
                object_width, 0.0,
                object_width, object_height,
                0.0, object_height], 2)
        self.set_index([0, 1, 3, 2])


class Shader():
    def __init__(self, context, vert_name, frag_name):
        self.shader = GstGL.GLShader.new(context)

        vert = open("shaders/%s" % vert_name).read()
        frag = open("shaders/%s" % frag_name).read()

        self.shader.set_vertex_source(vert)
        self.shader.set_fragment_source(frag)

        if not self.shader.compile():
            exit()

    def use(self):
        return self.shader.use()

    def get_handle(self):
        return self.shader.get_program_handle()

    def set_matrix(self, name, matrix):
        location = glGetUniformLocation(self.get_handle(), name)
        glUniformMatrix4fv(location, 1, GL_FALSE, matrix)


class CairoTexture():
    def __init__(self, gl_id, width, height):
        self.width, self.height = width, height
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.ctx = cairo.Context(self.surface)
        glActiveTexture(gl_id)
        self.texture_handle = glGenTextures(1)

    def draw(self, callback):
        glBindTexture(GL_TEXTURE_RECTANGLE, self.texture_handle)
        callback(self.ctx, self.width, self.height)
        glTexImage2D(GL_TEXTURE_RECTANGLE,
                     0,
                     GL_RGBA,
                     self.width,
                     self.height,
                     0,
                     GL_BGRA,
                     GL_UNSIGNED_BYTE,
                     self.surface.get_data())
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

    def delete(self):
        if self.texture_handle:
            glDeleteTextures(self.texture_handle)