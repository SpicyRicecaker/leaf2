#version 460
#extension GL_NV_mesh_shader : require
#extension GL_EXT_debug_printf : enable

#define PI 3.1415926538

layout(local_size_x = 4) in;
layout(triangles, max_vertices = 4, max_primitives = 2) out;

out vec3[] FragPos;
out vec3[] Normal;
out vec2[] TexCoord;

uniform mat4 view;
uniform mat4 projection;
uniform float t;
uniform float dt;

// assuming 1 unit is 1 meter
const float H = 0.13970;
const float W = 0.07785;

const float U = 0.955905511811 * H;
const float D = 0.044094488189 * H;
const float L = 0.311624919717 * W;
const float R = 0.688375080283 * W;
const int NUM_STEPS_PER_DT = 1;

// Simulated particle positions (4 particles)
// const vec3 positions[4] = vec3[](
//     vec3(-0.5,  0.5, 0.0),
//     vec3( 0.5,  0.5, 0.0),
//     vec3(-0.5, -0.5, 0.0),
//     vec3( 0.5, -0.5, 0.0)
// );
struct Sinusoid {
    float freq;
    float amp;
    float phase;
};

struct Leaf {
    vec3 position;
    float phi;
};

layout(binding = 0, std430) buffer ssbo0 {
    Leaf leaves[];
};

layout(binding = 1, std430) buffer ssbo1 {
    Sinusoid m01_G90_ux[];
};

layout(binding = 2, std430) buffer ssbo2 {
    Sinusoid m01_G90_uz[];
};

layout(binding = 3, std430) buffer ssbo3 {
    Sinusoid m01_G90_omy[];
};
// --------------------
// |       |          |
// |       |          |
// |      u|          |
// |       |          |
// |       |          |
// |  l    |    r     |
// |=======x==========|
// |       |          |
// |      d|          |
// |       |          |
// --------------------

// Quad vertex offsets relative to particle center
const vec2 quad_offsets[4] = vec2[](
    vec2(-L, -D), // bl
    vec2( R, -D), // br
    vec2(-L,  U), // tl
    vec2( R,  U)  // tr
);

const vec2 tex_coords[4] = vec2[](
    vec2(0., 1.),
    vec2(1., 1.),
    vec2(0., 0.),
    vec2(1., 0.)
);

// vvvvvvvvvvvvvvvvv[begin m01_G90_ux]vvvvvvvvvvvvvvvvv
float eval_m01_G90_ux(float t) {
    float sum = 0;
    for (int i = 0; i < m01_G90_ux.length(); i++) {
        sum += m01_G90_ux[i].amp * cos(2. * PI * m01_G90_ux[i].freq * t + m01_G90_ux[i].phase);
    }
    return sum;
};

float eval_m01_G90_uz(float t) {
    float sum = 0;
    for (int i = 0; i < m01_G90_uz.length(); i++) {
        sum += m01_G90_uz[i].amp * cos(2. * PI * m01_G90_uz[i].freq * t + m01_G90_uz[i].phase);
    }
    return sum;
};

float eval_m01_G90_omy(float t) {
    float sum = 0;
    for (int i = 0; i < m01_G90_omy.length(); i++) {
        sum += m01_G90_omy[i].amp * cos(2. * PI * m01_G90_omy[i].freq * t + m01_G90_omy[i].phase);
    }
    return sum;
};
// ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

// mat2 rotate2d(float _angle){

// }

vec3 rot_over_x_axis_by_90_cw(vec3 v) {
    return mat3( 1., 0., 0.,
                 0., 0., 1.,
                 0.,-1., 0.) * v;
}

mat3 rotate_over_z_axis_by_angle(float a) {
    return mat3( cos(a), -sin(a), 0.,
                 sin(a),  cos(a), 0.,
                 0.,               0.,              1.);
}

void main() {
    uint particle_idx = gl_WorkGroupID.x;
    uint vertex_idx = gl_LocalInvocationID.x;

    // r(t) = r(t-dt) + v(t-dt)dt
    for (int i = 0; i < NUM_STEPS_PER_DT; i++) {
        leaves[particle_idx].position.x += eval_m01_G90_ux(t - dt) * dt;
        leaves[particle_idx].position.y += eval_m01_G90_uz(t - dt) * dt;
        leaves[particle_idx].phi += eval_m01_G90_omy(t - dt) * dt;
    }

    // Determine the base position of this particle
    vec3 center = leaves[particle_idx].position.xyz;
    
    // Expand the vertex out into a quad
    vec4 pre_project = vec4(center + rot_over_x_axis_by_90_cw(vec3(quad_offsets[vertex_idx], 0.)) * rotate_over_z_axis_by_angle(leaves[particle_idx].phi), 1.);
    gl_MeshVerticesNV[vertex_idx].gl_Position = projection * view * pre_project;
    
    FragPos[vertex_idx] = pre_project.xyz; 
    Normal[vertex_idx] = rot_over_x_axis_by_90_cw(vec3(0, 0, 1));
    TexCoord[vertex_idx] = tex_coords[vertex_idx];

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