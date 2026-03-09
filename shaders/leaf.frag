#version 330 core

in vec3 FragPos;
in vec3 Normal;
in vec3 Color;

out vec4 FragColor;

uniform vec3 lightDir;
uniform vec3 lightColor;
uniform vec3 viewPos;

// Phong constants
const float ambientStrength  = 0.2;
const float specularStrength = 0.5;
const float shininess        = 32.0;

void main()
{
    vec3 norm     = normalize(Normal);
    vec3 lightD   = normalize(-lightDir);   // lightDir points FROM light, so negate

    // Ambient
    vec3 ambient  = ambientStrength * lightColor;

    // Diffuse
    float diff    = max(dot(norm, lightD), 0.0);
    vec3 diffuse  = diff * lightColor;

    // Specular (Blinn-Phong)
    vec3 viewDir  = normalize(viewPos - FragPos);
    vec3 halfDir  = normalize(lightD + viewDir);
    float spec    = pow(max(dot(norm, halfDir), 0.0), shininess);
    vec3 specular = specularStrength * spec * lightColor;

    vec3 result   = (ambient + diffuse + specular) * Color;
    FragColor     = vec4(result, 1.0);
}