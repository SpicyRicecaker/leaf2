import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import numpy as np

# 1. Mesh Shader Source
# It processes 4 threads per group. Each group makes 1 quad (4 vertices, 2 triangles).
mesh_shader_src = """
#version 450
#extension GL_NV_mesh_shader : require

layout(local_size_x = 4) in;
layout(triangles, max_vertices = 4, max_primitives = 2) out;

// Simulated particle positions (4 particles)
// const vec3 positions[4] = vec3[](
//     vec3(-0.5,  0.5, 0.0),
//     vec3( 0.5,  0.5, 0.0),
//     vec3(-0.5, -0.5, 0.0),
//     vec3( 0.5, -0.5, 0.0)
// );

layout(binding = 0, std430) readonly buffer ssbo0 {
    vec4 positions[];
};

// Quad vertex offsets relative to particle center
const vec2 quad_offsets[4] = vec2[](
    vec2(-0.1, -0.1),
    vec2( 0.1, -0.1),
    vec2(-0.1,  0.1),
    vec2( 0.1,  0.1)
);

void main() {
    uint particle_idx = gl_WorkGroupID.x;
    uint vertex_idx = gl_LocalInvocationID.x;

    // Determine the base position of this particle
    vec3 center = positions[particle_idx].xyz;
    
    // Expand the vertex out into a quad
    gl_MeshVerticesNV[vertex_idx].gl_Position = vec4(center.xy + quad_offsets[vertex_idx], center.z, 1.0);

    // Only thread 0 needs to define the topology (indices) for the 2 triangles
    if (vertex_idx == 0) {
        gl_PrimitiveCountNV = 2;
        
        // Triangle 1: Top-Left, Bottom-Left, Top-Right (0, 1, 2)
        gl_PrimitiveIndicesNV[0] = 0;
        gl_PrimitiveIndicesNV[1] = 1;
        gl_PrimitiveIndicesNV[2] = 2;
        
        // Triangle 2: Bottom-Left, Bottom-Right, Top-Right (1, 3, 2)
        gl_PrimitiveIndicesNV[3] = 1;
        gl_PrimitiveIndicesNV[4] = 3;
        gl_PrimitiveIndicesNV[5] = 2;
    }
}
"""

# 2. Fragment Shader Source
fragment_shader_src = """
#version 450
out vec4 fragColor;
void main() {
    fragColor = vec4(0.2, 0.6, 1.0, 1.0); // Pretty blue quads
}
"""

def main():
    # Initialize Pygame and OpenGL context
    pygame.init()
    pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
    glClearColor(0.1, 0.1, 0.1, 1.0)

    # Compile the shaders using modern stages
    # Note: PyOpenGL might require using raw glCompileShader for GL_MESH_SHADER_NV 
    # if compileShader macro doesn't recognize the token yet.
    GL_MESH_SHADER_NV = 0x9559
    mesh_shader = glCreateShader(GL_MESH_SHADER_NV)
    glShaderSource(mesh_shader, mesh_shader_src)
    glCompileShader(mesh_shader)
    # if not glGetShaderiv(mesh_shader, GL_COMPILE_STATUS):
    #     print(glGetShaderInfoLog(mesh_shader))
    #     return

    frag_shader = compileShader(fragment_shader_src, GL_FRAGMENT_SHADER)
    program = glCreateProgram()
    glAttachShader(program, mesh_shader)
    glAttachShader(program, frag_shader)
    glLinkProgram(program)

    # Setup a dummy VAO (Mesh shaders don't require VBOs if data is fetched/generated inside)
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)
    print('asdf')
    particles_buffer = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, particles_buffer)

    print("samity", particles_buffer)
    particles = np.array([
        [-0.5, 0.5, 0.0],
        [0.5, 0.5, 0.0],
        [-0.5, -0.5, 0.0],
        [0.5, -0.5, 0.0]
    ])
    particles = np.pad(particles, ((0, 0), (0, 1)))
    glBufferData(
        GL_SHADER_STORAGE_BUFFER,
        # float is 4 bytes, 4 floats is 16 bytes, 16 bytes * length
        16 * 4,
        particles.data,
        GL_DYNAMIC_DRAW
    )

    # Resolution handling for extension functions if needed
    try:
        from OpenGL.GL.NV.mesh_shader import glDrawMeshTasksNV
    except ImportError:
        # Fallback to direct resolution if wrapper is missing
        from ctypes import c_uint
        import OpenGL.platform as p
        glDrawMeshTasksNV = p.createExtensionFunction('glDrawMeshTasksNV', None, None, [c_uint, c_uint])

    # Main Loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(program)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, particles_buffer)        # Draw 4 mesh tasks (workgroups). Each workgroup handles 1 particle.
        # Arguments: (first task, count)
        glDrawMeshTasksNV(0, 4)

        pygame.display.flip()
        pygame.time.wait(10)

    pygame.quit()

if __name__ == '__main__':
    main()