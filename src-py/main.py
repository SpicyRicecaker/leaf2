import math
import sys
import os
import ctypes

import pygame
from pygame.locals import *

import numpy as np
import pyrr
import pygltflib
import base64

from OpenGL.GL import *
from OpenGL.GL import shaders

from graph import RealtimeGraph
from shared_clock import SharedClock
from framebar import FrameBar
from data_wrangler import DiscTransformPredictor

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WIN_W, WIN_H      = 1280, 720
FOV_DEG           = 70.0
NEAR, FAR         = 0.01, 1000.0

MOVE_SPEED        = 5.0
MOUSE_SENSITIVITY = 0.1

PLAYER_START      = pyrr.Vector3([0.0, 0.0, 6.0])
PLAYER_PITCH      =  0.0
PLAYER_YAW        = -90.0

LIGHT_DIR         = np.array([ 0.0, -1.0,  0.5], dtype=np.float32)
LIGHT_COLOR       = np.array([ 1.0,  1.0,  1.0], dtype=np.float32)

# ---------------------------------------------------------------------------
# Shader helpers  (unchanged)
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
# FBX loader  (replaces build_leaf_vbo)
# ---------------------------------------------------------------------------

def load_glb_mesh(glb_path: str) -> tuple[int, int, int, int]:
    """
    Load a GLB file (glTF binary) and upload to OpenGL.
    Returns (vao, vbo, ebo, index_count).
    Assumes single mesh, single primitive, Y-up (export with Y-up from Blender).
    """

    here = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(here, glb_path)

    gltf = pygltflib.GLTF2().load(full_path)

    # helper: pull raw bytes out of a bufferView by accessor index
    def get_accessor_data(accessor_idx: int) -> np.ndarray:
        accessor    = gltf.accessors[accessor_idx]
        buffer_view = gltf.bufferViews[accessor.bufferView]
        buffer      = gltf.buffers[0]

        # GLB stores binary chunk directly
        blob = gltf.binary_blob()

        start  = buffer_view.byteOffset or 0
        length = buffer_view.byteLength
        raw    = blob[start : start + length]

        # accessor component types
        COMPONENT_DTYPE = {
            5120: np.int8,
            5121: np.uint8,
            5122: np.int16,
            5123: np.uint16,
            5125: np.uint32,
            5126: np.float32,
        }
        TYPE_COUNT = {
            "SCALAR": 1,
            "VEC2":   2,
            "VEC3":   3,
            "VEC4":   4,
            "MAT4":  16,
        }

        dtype      = COMPONENT_DTYPE[accessor.componentType]
        n_comps    = TYPE_COUNT[accessor.type]
        acc_offset = accessor.byteOffset or 0

        arr = np.frombuffer(raw, dtype=dtype, offset=acc_offset)

        if n_comps > 1:
            arr = arr.reshape(-1, n_comps)

        return arr.copy()   # copy so it's writeable

    # --- grab the first mesh primitive ---
    primitive = gltf.meshes[0].primitives[0]

    positions = get_accessor_data(primitive.attributes.POSITION).astype(np.float32)
    normals   = get_accessor_data(primitive.attributes.NORMAL).astype(np.float32)
    uvs       = get_accessor_data(primitive.attributes.TEXCOORD_0).astype(np.float32)
    indices   = get_accessor_data(primitive.indices).astype(np.uint32).flatten()

    # sanity check
    print(f"[GLB] verts={len(positions)}  indices={len(indices)}")

    # interleave pos(3) + normal(3) + uv(2)
    vertex_data = np.hstack([positions, normals, uvs])  # (N, 8)

    # --- upload ---
    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    ebo = glGenBuffers(1)

    glBindVertexArray(vao)

    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

    stride = 8 * ctypes.sizeof(ctypes.c_float)

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)

    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(3 * ctypes.sizeof(ctypes.c_float)))
    glEnableVertexAttribArray(1)

    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(6 * ctypes.sizeof(ctypes.c_float)))
    glEnableVertexAttribArray(2)

    glBindVertexArray(0)

    return vao, vbo, ebo, len(indices)

def load_quad() -> tuple[int, int, int, int]:
    # --- upload ---
    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    ebo = glGenBuffers(1)

    glBindVertexArray(vao)

    positions = np.array([
        [ 1,  1, 0], #0
        [-1,  1, 0], #1
        [-1, -1, 0], #2
        [ 1 ,-1, 0], #3
        #[ 1,  1, 0], #4 
        #[-1,  1, 0], #5
        #[-1, -1, 0], #6
        #[ 1 ,-1, 0], #7
    ], dtype=np.float32)

    normals = np.array([
        [ 1, 0, 0],
        [ 1, 0, 0],
        [ 1, 0, 0],
        [ 1, 0, 0],
        #[-1, 0, 0],
        #[-1, 0, 0],
        #[-1, 0, 0],
        #[-1, 0, 0],
    ], dtype=np.float32)

    uvs = np.array([
        [ 1, 0],
        [ 0, 0],
        [ 0, 1],
        [ 1, 1],
        #[ 1, 0],
        #[ 0, 0],
        #[ 0, 1],
        #[ 1, 1],        
    ], dtype=np.float32)

    indices = np.array([
        0, 1, 2,
        2, 3, 0,
        #2+4, 1+4, 0+4,
        #0+4, 3+4, 2+4,
    ], dtype=np.int32)

    vertex_data = np.hstack([positions, normals, uvs])
        
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

    stride = 8 * ctypes.sizeof(ctypes.c_float)

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)

    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(3 * ctypes.sizeof(ctypes.c_float)))
    glEnableVertexAttribArray(1)

    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(6 * ctypes.sizeof(ctypes.c_float)))
    glEnableVertexAttribArray(2)

    glBindVertexArray(0)

    return vao, vbo, ebo, len(indices)

# ---------------------------------------------------------------------------
# Texture loader
# ---------------------------------------------------------------------------

def load_texture(image_path: str) -> int:
    """Load a jpg/png and upload to OpenGL. Returns texture ID."""

    surface = pygame.image.load(image_path)
    surface = pygame.transform.flip(surface, False, False)  # FlipUVs in assimp handles this
    img_data = pygame.image.tostring(surface, "RGBA", False)
    w, h     = surface.get_size()

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    glGenerateMipmap(GL_TEXTURE_2D)

    glBindTexture(GL_TEXTURE_2D, 0)
    return tex_id


# ---------------------------------------------------------------------------
# Camera  (unchanged)
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
# Leaf transform  — added Blender Y-up correction via extra X rotation
# ---------------------------------------------------------------------------

def compute_leaf_model_matrix(t: float, predictor, i) -> np.ndarray:
    x = predictor.x(i) * 2.5
    y = predictor.z(i) * 2.5

    translation = pyrr.matrix44.create_from_translation(
        pyrr.Vector3([x, y, -50]), dtype=np.float32)

    phi = predictor.phi(i)

    # Blender Z-up → OpenGL Y-up correction: rotate -90 deg around X
    rx_correct = pyrr.matrix44.create_from_x_rotation(np.radians(0), dtype=np.float32)

    rx    = pyrr.matrix44.create_from_x_rotation(0, dtype=np.float32)
    ry    = pyrr.matrix44.create_from_y_rotation(0, dtype=np.float32)
    rz    = pyrr.matrix44.create_from_z_rotation(phi, dtype=np.float32)

    rotation = pyrr.matrix44.multiply(
        rz,
        pyrr.matrix44.multiply(
            ry,
            pyrr.matrix44.multiply(rx, rx_correct)
        )
    )
 
    model = pyrr.matrix44.multiply(rotation, translation)
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
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    program = build_program("../shaders/leaf.vert", "../shaders/leaf.frag")

    # --- load FBX ---
    vao_l, vbo_l, ebo_l, index_count_l = load_glb_mesh("../art/american_elm.glb")  # <-- your fbx filename here
    vao_q, vbo_q, ebo_q, index_count_q = load_quad()

    # --- load texture ---
    tex_id_l = load_texture(os.path.abspath("art/american elm front flat.jpg"))  # <-- your path
    tex_id_q = load_texture(os.path.abspath("art/transparent_star.png"))  # <-- your path

    # --- uniforms ---
    u_model       = glGetUniformLocation(program, "model")
    u_view        = glGetUniformLocation(program, "view")
    u_projection  = glGetUniformLocation(program, "projection")
    u_lightDir    = glGetUniformLocation(program, "lightDir")
    u_lightColor  = glGetUniformLocation(program, "lightColor")
    u_viewPos     = glGetUniformLocation(program, "viewPos")
    u_leafTexture = glGetUniformLocation(program, "leafTexture")

    projection = pyrr.matrix44.create_perspective_projection_matrix(
        FOV_DEG, WIN_W / WIN_H, NEAR, FAR, dtype=np.float32)

    camera = Camera(PLAYER_START, PLAYER_PITCH, PLAYER_YAW)

    clock    = SharedClock()
    hwnd     = pygame.display.get_wm_info()["window"]
    framebar = FrameBar(clock, hwnd)
    framebar.start()

    mouse_captured = False
    clock_obj      = pygame.time.Clock()

    files = ["data_stable.mat", "data_m01_G90.mat", "data_m05_G160.mat", "data_m10_G150.mat"]
    disc_transform_predictor_1 = DiscTransformPredictor(files[2], 1 / 60)
    i_x = 0

    graph = RealtimeGraph(clock.get_time, disc_transform_predictor_1)
    graph.start()

    running = True
    while running:

        dt = clock_obj.tick(60) / 1000.0
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

        if not clock.is_paused():
            keys = pygame.key.get_pressed()
            camera.process_keyboard(keys, dt)
        keys = pygame.key.get_pressed()
        camera.process_keyboard(keys, dt)

        model = compute_leaf_model_matrix(t, disc_transform_predictor_1, i_x)
        view  = camera.get_view_matrix()

        glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)  # added COLOR_BUFFER_BIT
        glUseProgram(program)

        # bind texture to unit 0
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex_id_q)
        glUniform1i(u_leafTexture, 0)

        glUniformMatrix4fv(u_model,      1, GL_FALSE, model)
        glUniformMatrix4fv(u_view,       1, GL_FALSE, view)
        glUniformMatrix4fv(u_projection, 1, GL_FALSE, projection)
        glUniform3fv(u_lightDir,   1, LIGHT_DIR)
        glUniform3fv(u_lightColor, 1, LIGHT_COLOR)
        glUniform3fv(u_viewPos,    1, camera.position.astype(np.float32))

        # glBindVertexArray(vao_l)
        # glDrawElements(GL_TRIANGLES, index_count_l, GL_UNSIGNED_INT, None)
        # glBindVertexArray(0)

        glBindVertexArray(vao_q)
        glDrawElementsInstanced(GL_TRIANGLES, index_count_q, GL_UNSIGNED_INT, None, 99)
        glBindVertexArray(0)

        i_x += 1

        pygame.display.flip()

    glDeleteVertexArrays(1, [vao_l])
    glDeleteBuffers(1, [vbo_l])
    glDeleteBuffers(1, [ebo_l])
    glDeleteTextures(1, [tex_id_l])
    glDeleteProgram(program)
    graph.stop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
