#version 330 core

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform vec3      lightDir;
uniform vec3      lightColor;
uniform vec3      viewPos;
uniform sampler2D leafTexture;

const float ambientStrength  = 1.0;
const float specularStrength = 0.0;
const float shininess        = 0.0;
const float diffuseStrength = 0.15;

void main()
{
    vec3 norm   = normalize(Normal);
    vec3 lightD = normalize(-lightDir);

    // detect back face — normal points away from camera
    vec3  viewDir   = normalize(viewPos - FragPos);
    bool  isBack    = dot(norm, viewDir) < 0.0;

    // flip normal for lighting on back face
    if (isBack) norm = -norm;

    // Ambient
    vec3 ambient  = ambientStrength * lightColor;

    // Diffuse
    float diff    = max(dot(norm, lightD), 0.0);
    vec3  diffuse = diffuseStrength * diff * lightColor;

    // Specular
    vec3  halfDir = normalize(lightD + viewDir);
    float spec    = pow(max(dot(norm, halfDir), 0.0), shininess);
    vec3  specular = specularStrength * spec * lightColor;

    vec3 texColor = texture(leafTexture, TexCoord).rgb;

    // lighten back face
    // if (isBack) texColor = mix(texColor, vec3(1.0), 0.35);
    if (isBack) texColor = texColor;

    vec3 result = (ambient + diffuse + specular) * texColor;
    FragColor   = vec4(result, 1.0);
}