import math
import sys
import os
import ctypes

import pygame
from pygame.locals import *

import numpy as np
import pyrr

from OpenGL.GL import *
from OpenGL.GL import shaders

from graph import RealtimeGraph
from shared_clock import SharedClock
from framebar import FrameBar

from data_wrangler import DiscTransformPredictor
# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WIN_W, WIN_H       = 1280, 720
FOV_DEG            = 70.0
NEAR, FAR          = 0.01, 1000.0

MOVE_SPEED         = 5.0
MOUSE_SENSITIVITY  = 0.1

FALL_DURATION      = 5.0
LEAF_START_Y       =  4.0
LEAF_END_Y         = -2.0
LEAF_X             =  0.0
LEAF_Z             =  0.0

PLAYER_START       = pyrr.Vector3([0.0, 0.0,  6.0])
PLAYER_PITCH       =  0.0
PLAYER_YAW         = -90.0

LIGHT_DIR          = np.array([ 0.3, -1.0,  0.5], dtype=np.float32)
LIGHT_COLOR        = np.array([ 1.0,  1.0,  1.0], dtype=np.float32)

COLOR_FRONT = np.array([0.2, 0.7, 0.15], dtype=np.float32)
COLOR_BACK  = np.array([0.8, 0.75, 0.1], dtype=np.float32)

# ---------------------------------------------------------------------------
# Shader helpers
# ---------------------------------------------------------------------------

def load_shader_source(path: str) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, path), "r") as f:
        return f.read()


def build_program(vert_path: str, frag_path: str) -> int:
    vert_src = load_shader_source(vert_path)
    frag_src = load_shader_source(frag_path)
    vert     = shaders.compileShader(vert_src, GL_VERTEX_SHADER)
    frag     = shaders.compileShader(frag_src, GL_FRAGMENT_SHADER)
    program  = shaders.compileProgram(vert, frag)
    return int(program)

# ---------------------------------------------------------------------------
# Leaf geometry
# ---------------------------------------------------------------------------

def build_leaf_vbo() -> tuple[int, int, int]:
    hs = 0.5

    tl = [-hs,  hs, 0.0]
    tr = [ hs,  hs, 0.0]
    br = [ hs, -hs, 0.0]
    bl = [-hs, -hs, 0.0]

    nf = [0.0, 0.0,  1.0]
    nb = [0.0, 0.0, -1.0]

    cf = COLOR_FRONT.tolist()
    cb = COLOR_BACK.tolist()

    def v(pos, n, c):
        return pos + n + c

    vertices = [
        v(tl, nf, cf), v(bl, nf, cf), v(br, nf, cf),
        v(tl, nf, cf), v(br, nf, cf), v(tr, nf, cf),
        v(tl, nb, cb), v(br, nb, cb), v(bl, nb, cb),
        v(tl, nb, cb), v(tr, nb, cb), v(br, nb, cb),
    ]

    data = np.array(vertices, dtype=np.float32).flatten()

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)

    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)

    stride = 9 * ctypes.sizeof(ctypes.c_float)

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)

    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(3 * ctypes.sizeof(ctypes.c_float)))
    glEnableVertexAttribArray(1)

    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(6 * ctypes.sizeof(ctypes.c_float)))
    glEnableVertexAttribArray(2)

    glBindVertexArray(0)

    return vao, vbo, len(vertices)

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

class Camera:
    def __init__(self, position: pyrr.Vector3, pitch: float, yaw: float):
        self.position = np.array(position, dtype=np.float64)
        self.pitch    = pitch
        self.yaw      = yaw

    def get_front(self) -> np.ndarray:
        p = math.radians(self.pitch)
        y = math.radians(self.yaw)
        front = np.array([
            math.cos(p) * math.cos(y),
            math.sin(p),
            math.cos(p) * math.sin(y),
        ], dtype=np.float64)
        return front / np.linalg.norm(front)

    def get_right(self) -> np.ndarray:
        front    = self.get_front()
        world_up = np.array([0.0, 1.0, 0.0])
        right    = np.cross(front, world_up)
        return right / np.linalg.norm(right)

    def get_view_matrix(self) -> np.ndarray:
        pos   = self.position.astype(np.float32)
        front = self.get_front().astype(np.float32)
        up    = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        return pyrr.matrix44.create_look_at(pos, pos + front, up)

    def process_mouse(self, dx: float, dy: float):
        self.yaw   += dx * MOUSE_SENSITIVITY
        self.pitch -= dy * MOUSE_SENSITIVITY
        self.pitch  = max(-89.0, min(89.0, self.pitch))

    def process_keyboard(self, keys, dt: float):
        speed    = MOVE_SPEED * dt
        front    = self.get_front()
        right    = self.get_right()
        world_up = np.array([0.0, 1.0, 0.0], dtype=np.float64)

        front_xz = np.array([front[0], 0.0, front[2]], dtype=np.float64)
        norm = np.linalg.norm(front_xz)
        if norm > 1e-6:
            front_xz /= norm

        right_xz = np.array([right[0], 0.0, right[2]], dtype=np.float64)
        norm = np.linalg.norm(right_xz)
        if norm > 1e-6:
            right_xz /= norm

        if keys[K_w]:      self.position += front_xz * speed
        if keys[K_s]:      self.position -= front_xz * speed
        if keys[K_a]:      self.position -= right_xz * speed
        if keys[K_d]:      self.position += right_xz * speed
        if keys[K_SPACE]:  self.position += world_up * speed
        if keys[K_LSHIFT]: self.position -= world_up * speed

# ---------------------------------------------------------------------------
# Leaf transform
# ---------------------------------------------------------------------------

def compute_leaf_model_matrix(t: float, predictor, i) -> np.ndarray:
    x = predictor.x(i) * 2.5
    y = predictor.z(i) * 2.5

    translation = pyrr.matrix44.create_from_translation(
        pyrr.Vector3([x, y, -50]), dtype=np.float32)

    # angle = math.sin(2.0 * math.pi * t)
    # phi is the angle from disc normal to gravitational up 
    phi = predictor.phi(i)

    # not sure why the matrices for y and z seem reversed here
    rx    = pyrr.matrix44.create_from_x_rotation(np.radians(90), dtype=np.float32)
    ry    = pyrr.matrix44.create_from_y_rotation(-phi, dtype=np.float32)
    rz    = pyrr.matrix44.create_from_z_rotation(0, dtype=np.float32)

    rotation = pyrr.matrix44.multiply(rz, pyrr.matrix44.multiply(ry, rx))
    model    = pyrr.matrix44.multiply(rotation, translation)
    return model

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    pygame.display.set_caption("Leaf")

    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(
        pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)

    screen = pygame.display.set_mode((WIN_W, WIN_H), DOUBLEBUF | OPENGL)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_MULTISAMPLE)
    glDisable(GL_CULL_FACE)
    glViewport(0, 0, WIN_W, WIN_H)
    glClearColor(0.53, 0.81, 0.92, 1.0)

    program               = build_program("shaders/leaf.vert", "shaders/leaf.frag")
    vao, vbo, vertex_count = build_leaf_vbo()

    u_model      = glGetUniformLocation(program, "model")
    u_view       = glGetUniformLocation(program, "view")
    u_projection = glGetUniformLocation(program, "projection")
    u_lightDir   = glGetUniformLocation(program, "lightDir")
    u_lightColor = glGetUniformLocation(program, "lightColor")
    u_viewPos    = glGetUniformLocation(program, "viewPos")

    projection = pyrr.matrix44.create_perspective_projection_matrix(
        FOV_DEG, WIN_W / WIN_H, NEAR, FAR, dtype=np.float32)

    camera = Camera(PLAYER_START, PLAYER_PITCH, PLAYER_YAW)

    # --- shared clock  --------------------------------------------------
    clock = SharedClock()

    # --- framebar  ------------------------------------------------------
    hwnd     = pygame.display.get_wm_info()["window"]
    framebar = FrameBar(clock, hwnd)
    framebar.start()

    # --- state  ---------------------------------------------------------
    mouse_captured = False
    clock_obj      = pygame.time.Clock()

    files = ["data_m01_G90.mat", "data_m05_G160.mat", "data_m10_G150.mat"]
    disc_transform_predictor_1 = DiscTransformPredictor(files[1], 1 / 60)
    i_x = 0

    # --- graph  ---------------------------------------------------------
    graph = RealtimeGraph(clock.get_time, disc_transform_predictor_1)
    graph.start()

    # --- main loop  -----------------------------------------------------
    running = True
    while running:
 
        dt = clock_obj.tick(60) / 1000.0
        # dt = min(dt, 0.05)
        t  = clock.get_time()

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

                elif event.key == K_f:
                    mouse_captured = not mouse_captured
                    if mouse_captured:
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                    else:
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)

                elif event.key == K_SPACE:
                    clock.toggle_pause()

                elif event.key == K_RIGHT:
                    clock.step_frames(1)

                elif event.key == K_LEFT:
                    clock.step_frames(-1)
                
                elif event.key == K_r:
                    clock.reset()

            elif event.type == MOUSEMOTION and mouse_captured:
                dx, dy = event.rel
                camera.process_mouse(float(dx), float(dy))


        # only move camera when not paused / scrubbing
        if not clock.is_paused():
            keys = pygame.key.get_pressed()
            camera.process_keyboard(keys, dt)
        # Move camera independently of simulation pause state
        keys = pygame.key.get_pressed()
        camera.process_keyboard(keys, dt)

        model = compute_leaf_model_matrix(t, disc_transform_predictor_1, i_x)
        view  = camera.get_view_matrix()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(program)

        glUniformMatrix4fv(u_model,      1, GL_FALSE, model)
        glUniformMatrix4fv(u_view,       1, GL_FALSE, view)
        glUniformMatrix4fv(u_projection, 1, GL_FALSE, projection)
        glUniform3fv(u_lightDir,   1, LIGHT_DIR)
        glUniform3fv(u_lightColor, 1, LIGHT_COLOR)
        glUniform3fv(u_viewPos,    1, camera.position.astype(np.float32))

        glBindVertexArray(vao)
        glDrawArrays(GL_TRIANGLES, 0, vertex_count)
        glBindVertexArray(0)

        # update state
        i_x += 1

        pygame.display.flip()

    glDeleteVertexArrays(1, [vao])
    glDeleteBuffers(1, [vbo])
    glDeleteProgram(program)
    graph.stop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()