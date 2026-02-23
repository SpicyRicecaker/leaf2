#import "conf.typ": *
#show: arkheion.with(
  title: "Thesis",
  abstract: "An abstract",
  authors: (
    (name: "Shengdong Li", email: "lishen@oregonstate.edu", affiliation: "Oregon State University"),
  ),
  date: "May 2, 2025",
  acknowledgements: "An undergraduate thesis advised by Mike Bailey
submitted to the Department of Physics, Oregon State University
in partial fulfillment of the requirements for the degree of Bachelor of Science in Physics",
  figuress: image("figures/OSU Logo.pdf", width: 50%),
)

#show ref: it => {
  set text(blue)
  it
}

#outline()


= intro
= background
== theory

(i) current realtime requirements for games seems to have caused games to not venture into the territory of simulating leaf movement. Rather, leaf movement seems to consist of arbitrary linear movement and rotation.
(ii) empirical measurement (along with full fluid solves of falling objects under the Navier-Stokes equations) of flat falling objects, especially disks, have revealed the energy of the fluid surrounding falling objects, depending on the Reynolds number (which factors in viscocity of fluid and speed of falling object) can have a dramatic effect on the rotation and movement of a falling object. For flat discs, these culminate in 4 or more regimes of movement, which are (1) steady, (2) fluttering (3) tumbling (4) chaotic (a combination of fluttering and tumbling). 
(iii) recently, there have been attempts made to simulate moving bodies in water capturing the complex movement of falling bodies (Soliman et. all 2024) while considering the energy of the local fluid around objects, precomputing as many values as possible and making approximations to achieve linear time simulation. But the logic is complex and some movement regimes still fail to be captured.
(iv) recent advances in raytracing such as ReSTIR have biased the probability distribution of the angle of reflected light toward light sources to simulate a photorealistic scene, to great performance and aesthetic results. Can we apply this to leaf simulations? 
(v) how realistic and performant would a simulation making use of the empirical probability distributions from literature of
    (1) final leaf position
    (2) leaf xyz translational velocity over time
    (3) leaf xyz angular velocity over time
    work to simulate a leaf's falling?
(vi) background on probability density function approximation techniques, and methods for selecting items from a complex probability density distribution programmatically.

Soliman et. all @soliman simulated the movement of various objects in fluid by making an approximation of lift and drag using emperical data from two types of rower's oars @caplan under water, and an approximation of the energy of the surrounding fluid using a local added mass approach. More precisely, they approximate how a 3D object under rotation in an arbitrary direction affects the energy of the fluid in the surrounding medium, with the added constraint that the velocity of fluid at a boundary must be the same as the velocity of the shape. They create an expression for the "added mass tensor", which yields an expression for energy. They approximate this "added mass tensor" through empirical observation of a few primitives, from which they extract a constant that best represents the shapes they analyzed. The resulting mass tensor was used with the Lagrangian and various integrational methods to simulate the trajectory of various objects. Their method is fast because they can precompute the expensive added mass tensor (given that the simulated body is rigid) before simulation, and during simulation the next position of the object can be calculated in linear time, which has implications for real-time applications such as games or simluations. They are able to successfully capture complex motion such as the autorotation of a maple seed that pure lift and drag analysis would not capture. While their model doesn't capture the chaotic and stable falling regimes of a falling leaf, their method paves the way to convincingly visualize the behavior of various objects in air and other fluids without costly fluid simulations.

== methods

create a pdf based off leaf parameters given experimental data 
    (1) final leaf position (falling coins et. all)
    (2) leaf xyz translational velocity over time (falling coins et. all and others)
    (3) leaf xyz angular velocity over time (falling coins et. all and others)

=== extraction of empirical data for (1)

For each paper, the falling coins et. all final position pdf for each regime was maximized via an image editor. The points were then hand-selected via specific pixel by painting a single pixel on a new layer. The mask layer was exported and run through a program to identify all marked pixels, and scaled to physical units from pixels. Find the full list of picked points in the supplementary material, as well as a website to visualize the points (here).

The resulting points were used to construct a PDF by kernel estimation method of PDFs, using a 2d gaussian kernel of size n as the kernel. 

(picture of resulting 3D probability density function here).

=== extraction of empirical data for (2)

Choosing of (1) enforces a constraint on the list of possible translational trajectories over time. From falling coins et. all (or others), the graph for translational z velocity over time for the specific regime was found. We make a sinusoidal approximation here, and manually measure the period, amplitude, and offset of the wave to be xyz given input parameters xyz. Then the average velocity over one full period was identified, and the starting height divides this to find the total time to fall. 

Based on the selection of (1) and the new time constraint, the translational x and y velocities have a set restriction. We also make a sinusoidal approximation for the translation x and y velocities. The amplitude and the frequency are scaled by a step of x, one after the other, repeatedly and randomly (to a range of a), until the ends align with the selection of 1.

=== extraction of empirical data for (3)

Choosing of (3)

== analytical procedure

sample each pdf for a given time step
repeat trials 1000x

apply graph to 3D simulated leaf
observe motion

== experimental setup

== procedure

= results

The resulting leaf simulation was run 
- 100 times in the steady regime
- 100 times in the fluttering regime
- 100 times in the tumbling regime
- 100 times in the chaotic regime

The 
compare measured outputs and sampling, verify PDFs are 90% accurate

    = rand result
    = analysis

= discussion
= conclusion
= acknowledgements

#bibliography("bibliography.bib")
