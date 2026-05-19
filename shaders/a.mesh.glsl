#version 460
#extension GL_NV_mesh_shader : require

layout(local_size_x = 4) in;
layout(triangles, max_vertices = 4, max_primitives = 2) out;

uniform mat4 view;
uniform mat4 projection;

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
    vec4 pre_project = vec4(center.xy + quad_offsets[vertex_idx], center.z, 1.0);
    gl_MeshVerticesNV[vertex_idx].gl_Position = projection * view * pre_project;

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