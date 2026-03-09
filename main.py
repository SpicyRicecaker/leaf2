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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WIN_W, WIN_H       = 1280, 720
FOV_DEG            = 70.0
NEAR, FAR          = 0.01, 1000.0

MOVE_SPEED         = 5.0          # units / second  (minecraft-like fly)
MOUSE_SENSITIVITY  = 0.1          # degrees per pixel

FALL_DURATION      = 5.0          # seconds for one fall cycle
LEAF_START_Y       =  4.0         # world-space Y where leaf spawns
LEAF_END_Y         = -2.0         # world-space Y where fall ends
LEAF_X             =  0.0
LEAF_Z             =  0.0

PLAYER_START       = pyrr.Vector3([0.0, 0.0,  6.0])  # behind leaf on +Z axis
PLAYER_PITCH       =  0.0         # degrees, looking straight ahead
PLAYER_YAW         = -90.0        # degrees, facing -Z (toward leaf)

LIGHT_DIR          = np.array([ 0.3, -1.0,  0.5], dtype=np.float32)  # sun angle
LIGHT_COLOR        = np.array([ 1.0,  1.0,  1.0], dtype=np.float32)

# Leaf colours
COLOR_FRONT = np.array([0.2, 0.7, 0.15], dtype=np.float32)   # green
COLOR_BACK  = np.array([0.8, 0.75, 0.1], dtype=np.float32)   # yellow-gold

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
#
#  The quad lives in the XY-plane, centred at the origin, size 1×1.
#  We store it as two back-to-back triangles for each side (12 vertices total).
#
#  Front side  (+Z normal)  — green
#  Back  side  (-Z normal)  — yellow
#
#  Each vertex: [x, y, z,  nx, ny, nz,  r, g, b]  (9 floats)
# ---------------------------------------------------------------------------

def build_leaf_vbo() -> tuple[int, int, int]:
    """Returns (vao, vbo, vertex_count)."""

    hs = 0.5  # half-size

    # corners (CCW from front)
    tl = [-hs,  hs, 0.0]
    tr = [ hs,  hs, 0.0]
    br = [ hs, -hs, 0.0]
    bl = [-hs, -hs, 0.0]

    nf = [0.0, 0.0,  1.0]   # front normal
    nb = [0.0, 0.0, -1.0]   # back normal

    cf = COLOR_FRONT.tolist()
    cb = COLOR_BACK.tolist()

    # Front face  (two triangles, CCW when viewed from +Z)
    #   tri1: tl, bl, br
    #   tri2: tl, br, tr
    # Back face   (CCW when viewed from -Z  →  reverse winding)
    #   tri1: tl, br, bl
    #   tri2: tl, tr, br

    def v(pos, n, c):
        return pos + n + c

    vertices = [
        # --- front ---
        v(tl, nf, cf), v(bl, nf, cf), v(br, nf, cf),
        v(tl, nf, cf), v(br, nf, cf), v(tr, nf, cf),
        # --- back  ---
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

    # location 0 : position
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)

    # location 1 : normal
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(3 * ctypes.sizeof(ctypes.c_float)))
    glEnableVertexAttribArray(1)

    # location 2 : color
    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(6 * ctypes.sizeof(ctypes.c_float)))
    glEnableVertexAttribArray(2)

    glBindVertexArray(0)

    return vao, vbo, len(vertices)

# ---------------------------------------------------------------------------
# Camera  (Minecraft-style fly: roll=0, pitch, yaw)
# ---------------------------------------------------------------------------

class Camera:
    def __init__(self, position: pyrr.Vector3, pitch: float, yaw: float):
        self.position = np.array(position, dtype=np.float64)
        self.pitch    = pitch   # degrees,  clamped ±89
        self.yaw      = yaw     # degrees

    # ------------------------------------------------------------------
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
        front = self.get_front()
        world_up = np.array([0.0, 1.0, 0.0])
        right = np.cross(front, world_up)
        return right / np.linalg.norm(right)

    def get_up(self) -> np.ndarray:
        # In Minecraft fly you move in world-Y for up/down,
        # but the camera's own up is derived normally
        front = self.get_front()
        right = self.get_right()
        up    = np.cross(right, front)
        return up / np.linalg.norm(up)

    # ------------------------------------------------------------------
    def get_view_matrix(self) -> np.ndarray:
        pos   = self.position.astype(np.float32)
        front = self.get_front().astype(np.float32)
        up    = np.array([0.0, 1.0, 0.0], dtype=np.float32)  # world up for look-at
        return pyrr.matrix44.create_look_at(pos, pos + front, up)

    # ------------------------------------------------------------------
    def process_mouse(self, dx: float, dy: float):
        self.yaw   += dx * MOUSE_SENSITIVITY
        self.pitch -= dy * MOUSE_SENSITIVITY          # dy inverted (screen vs world)
        self.pitch  = max(-89.0, min(89.0, self.pitch))

    # ------------------------------------------------------------------
    def process_keyboard(self, keys, dt: float):
        speed  = MOVE_SPEED * dt
        front  = self.get_front()
        right  = self.get_right()
        world_up = np.array([0.0, 1.0, 0.0], dtype=np.float64)

        # Horizontal movement uses front projected onto XZ plane (Minecraft-like)
        front_xz = np.array([front[0], 0.0, front[2]], dtype=np.float64)
        norm = np.linalg.norm(front_xz)
        if norm > 1e-6:
            front_xz /= norm

        right_xz = np.array([right[0], 0.0, right[2]], dtype=np.float64)
        norm = np.linalg.norm(right_xz)
        if norm > 1e-6:
            right_xz /= norm

        if keys[K_w]:
            self.position += front_xz * speed
        if keys[K_s]:
            self.position -= front_xz * speed
        if keys[K_a]:
            self.position -= right_xz * speed
        if keys[K_d]:
            self.position += right_xz * speed
        if keys[K_SPACE]:
            self.position += world_up * speed
        if keys[K_LSHIFT]:
            self.position -= world_up * speed

# ---------------------------------------------------------------------------
# Leaf transform
# ---------------------------------------------------------------------------

def compute_leaf_model_matrix(t: float) -> np.ndarray:
    """
    t  : elapsed time in seconds (continuous, not clamped)

    Fall:  linear interpolation from LEAF_START_Y → LEAF_END_Y over FALL_DURATION,
           then loops.

    Rotation: each axis rotated by sin(2π t) radians  (period = 1 second).
    """

    # --- fall  -----------------------------------------------------------
    cycle   = t % FALL_DURATION                          # 0 … FALL_DURATION
    alpha   = cycle / FALL_DURATION                      # 0 … 1
    y       = LEAF_START_Y + alpha * (LEAF_END_Y - LEAF_START_Y)

    translation = pyrr.matrix44.create_from_translation(
        pyrr.Vector3([LEAF_X, y, LEAF_Z]),
        dtype=np.float32,
    )

    # --- rotation  -------------------------------------------------------
    angle = math.sin(2.0 * math.pi * t)   # -1 … +1  radians, period = 1 s

    rx = pyrr.matrix44.create_from_x_rotation(angle, dtype=np.float32)
    ry = pyrr.matrix44.create_from_y_rotation(angle, dtype=np.float32)
    rz = pyrr.matrix44.create_from_z_rotation(angle, dtype=np.float32)

    rotation = pyrr.matrix44.multiply(rz, pyrr.matrix44.multiply(ry, rx))

    # model = T * R   (rotate first, then translate)
    model = pyrr.matrix44.multiply(rotation, translation)

    return model

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # --- pygame / OpenGL init -------------------------------------------
    pygame.init()
    pygame.display.set_caption("Leaf")

    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(
        pygame.GL_CONTEXT_PROFILE_MASK,
        pygame.GL_CONTEXT_PROFILE_CORE,
    )
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)

    screen = pygame.display.set_mode(
        (WIN_W, WIN_H),
        DOUBLEBUF | OPENGL,
    )

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_MULTISAMPLE)
    # We draw both sides explicitly via separate vertices, so no face culling.
    glDisable(GL_CULL_FACE)

    glViewport(0, 0, WIN_W, WIN_H)
    glClearColor(0.53, 0.81, 0.92, 1.0)   # sky blue

    # --- build GPU resources  -------------------------------------------
    program    = build_program("shaders/leaf.vert", "shaders/leaf.frag")
    vao, vbo, vertex_count = build_leaf_vbo()

    # uniform locations
    u_model      = glGetUniformLocation(program, "model")
    u_view       = glGetUniformLocation(program, "view")
    u_projection = glGetUniformLocation(program, "projection")
    u_lightDir   = glGetUniformLocation(program, "lightDir")
    u_lightColor = glGetUniformLocation(program, "lightColor")
    u_viewPos    = glGetUniformLocation(program, "viewPos")

    # projection matrix (constant)
    projection = pyrr.matrix44.create_perspective_projection_matrix(
        FOV_DEG,
        WIN_W / WIN_H,
        NEAR,
        FAR,
        dtype=np.float32,
    )

    # --- camera  --------------------------------------------------------
    camera = Camera(PLAYER_START, PLAYER_PITCH, PLAYER_YAW)

    # --- state  ---------------------------------------------------------
    mouse_captured = False
    clock          = pygame.time.Clock()
    start_ticks    = pygame.time.get_ticks()

    # --- main loop  -----------------------------------------------------
    running = True
    while running:

        dt      = clock.tick(0) / 1000.0   # uncapped, seconds
        dt      = min(dt, 0.05)            # clamp to avoid spiral of death
        t       = (pygame.time.get_ticks() - start_ticks) / 1000.0

        # --- events  ----------------------------------------------------
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

            elif event.type == MOUSEMOTION and mouse_captured:
                dx, dy = event.rel
                camera.process_mouse(float(dx), float(dy))

        # --- keyboard movement  -----------------------------------------
        keys = pygame.key.get_pressed()
        camera.process_keyboard(keys, dt)

        # --- compute matrices  ------------------------------------------
        model = compute_leaf_model_matrix(t)
        view  = camera.get_view_matrix()

        # --- render  ----------------------------------------------------
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(program)

        # upload uniforms
        glUniformMatrix4fv(u_model,      1, GL_FALSE, model)
        glUniformMatrix4fv(u_view,       1, GL_FALSE, view)
        glUniformMatrix4fv(u_projection, 1, GL_FALSE, projection)
        glUniform3fv(u_lightDir,   1, LIGHT_DIR)
        glUniform3fv(u_lightColor, 1, LIGHT_COLOR)
        glUniform3fv(u_viewPos,    1, camera.position.astype(np.float32))

        glBindVertexArray(vao)
        glDrawArrays(GL_TRIANGLES, 0, vertex_count)
        glBindVertexArray(0)

        pygame.display.flip()

    # --- cleanup  -------------------------------------------------------
    glDeleteVertexArrays(1, [vao])
    glDeleteBuffers(1, [vbo])
    glDeleteProgram(program)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()