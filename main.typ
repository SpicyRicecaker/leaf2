#import "conf.typ": *
#show: arkheion.with(
  title: "Thesis",
  abstract: "We attempt to simulate the visual aesthetics and kinetic motion of a falling leaf with high fidelity. We took a 2D scan of a real leaf and modeled the simulated leaf based off of the model. We analyzed literature to find the empirically observed characteristics of falling leaves that contribute to their dynanicism. We overview 4 specific falling regimes falling objects in fluid commonly undergo. We created a simple predictive model to replicate the motion in 3 of the 4 falling regimes. Our motion has the characteristic of being periodic and arrives at an end destination that is representative of what is observed literature.",
  authors: (
    (name: "Shengdong Li", email: "lishen@oregonstate.edu", affiliation: "Oregon State University"),
  ),
  date: "March 3, 2026",
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


= Introduction

The falling of leaves can greatly add to the emotion, tone, and ambiance of games. 

However, naive methods to fully and accurately simulate the movement of a leaf in air seem to require full solves of the Navier-Stokes fluid equation of the air interacting with the leaf. Games have a unique realtime requirement. This complexity of simulating the air fluid for leaves seems to have been a limiting factor for realistic leaf movement in games; many popular games made in the last few years such as Sekiro seems to consist of leaf movement with arbitrary linear movement and rotation.

Recently, there have been attempts made to simulate moving bodies in fluid which begin to capture the complex movement of falling bodies with the realtime requirement in mind. Soliman et. all @soliman focused on the local energy of the fluid surrounding objects, precomputing as many values as possible and making approximations to achieve linear time simulation. But the logic is complex, and some movement regimes still fail to be captured.

Can we approach the simulation problem from another perspective? The history of fluid mechanics has been rich with empirical observation, only made more practical and accessible over time with the advancement of technology and sensors. Several studies have been done on falling discs in fluid (@heisinger, @zhong). For flat discs, (while there have been discoveries of intermediary states), much of literature agrees on 4 primary regimes of movement, which are (1) steady, (2) fluttering (3) tumbling (4) chaotic (a combination of fluttering and tumbling) (@heisinger, @zhong).

#figure(
  image("assets/image-7.png"),
  caption: [The four primary regimes of leaf movement. Figure taken from Figure 2 of Coins Falling in Water (2013) @heisinger.],
) <heisingers_regimes>

The deciding of each regime seems to depend primarily on two factors, the Reynold's Number Re (or alternatively the Galileo Number) --- which factors in viscocity of fluid and speed of falling object --- and the Moment of Inertia of the disc in question (often denoted converted to a dimensionless quantity and denoted $I^*$). In other words, we have a good idea of _how_ to obtain a specific leaf trajectory, and additionally, we have some ideas of qualitative and quantitative values with which to _evaluate_ the trajectory of a leaf, once we obtain that trajectory.

In 2013, @dusek simulated the falling of disc in fluid with various parameteres of Galileo Number and $I*$, via a full solve of the Navier-Stokes equations. They obtained data with good agreement with empirical observations of nature.

As use of probabilistic models to predict physics in computer graphics has been a trend could we apply this to leaf simulations? Could we distill the information in numerical simulations to create a performant visualization for the game use case? How realistic and performant would a simulation making use of the empirical data from literature of (1) horizontal disc velocity over time (2) vertical disc velocity over time and (3) disc angular velocity over time simulate the falling trajectory of a leaf in air?

= Methods

== Obtaining a 3D Model for a Leaf

An autumn elm leaf in OSU campus was collected and allowed to sit betwixt book pages for one week. The resulting leaf was placed in a high-quality printer scanner. The picture was imported into Blender, where the edge outlines of the leaf were manually traced, the majority of the leaf's surface area filled in via _grid fill_, and the remainder manually adjusted to ensure there were no crossing edges in the resulting mesh.

== Gathering of Empirical Data for Simulation

One-shot high-precision time-series values for horizontal velocity, vertical velocity, and angular velocity relative to the trajectory plane were requested from one of the authors of @dusek.

#figure(
  table(
    columns: (1fr, 1fr, 1fr, 1fr, 1fr),
    inset: 10pt,
    align: horizon,
    table.header([Scenario], [$I^*$], [$"Re"$], [$t slash d$], [$h slash d space (plus.minus 0.002)$]),
    [A], [$1 times 10^1$], [$5 times 10^3$], [19.5], [19.5],
    [B], [-3], [1.0], [19.5], [19.5],
    [D], [-2], [0.5], [19.5], [19.5],
  ),
  caption: [Parameters for the three scenarioes presented in @heisingers_plot. $I^*$ is the dimensionless moment of inertia. Re is the Reynold's number. $t slash d$ is the dimensionless thickness of disc over diameter of disc. $h slash d$ is the dimensionless height of drop of disc over the diameter of the disc.],
)

The data had the parameters, based on the regime
  - Fluttering Periodic
    - $m^*=0.1$ $G=90$
  - Tumbling
    - $m^*=0.5$ $G=160$ (low non-dimensionalized mass)
    - $m^*=10$ $G=150$ (high non-dimensionalized mass)

- For the stable regime, no empirical data was found, and the the leaf is was assumed to be at terminal velocity in the fluid with a constant velocity in the direction of gravity.

- The chaotic regime, a combination of fluttering and tumbling, was not evaluated in this paper, due to difficulties establishing a valid quantitative analysis method. Look to the discussion for further details.

- $m^*$ is known as the "non-dimensionalized mass", defined as
$
  m^* = m/(rho d^3)
$
where $m$ represents the mass of the object, $rho$ represents the density of the fluid in which the object is moving in, and $d$ represents the diameter of the object.
- $G$ is known as the Galileo Number. Similar to the Reynolds Number commonly used in fluid mechanics, it scales with the length or volume of the object, and scales inversely with the viscocity of the fluid. A higher Galileo Number implies that a falling object is less affected by the turbulence of fluid.


== Simulation Procedure

@dusek

- Data for translation and angular velocities were provided in discrete time steps
- We linearly interpolate values between discrete time steps
- Leaf simulation has a fixed time step of 16.67 ms
- We take 10 simulation steps using a naive euler integration method, using a binary search to select to for the relevant discrete data points to interpolate between

== Analytical Procedure

We evaluate the simulation at each of the regimes.
For each regime, we look at the horizontal position over time, and qualitatively look for evidence of periodicity in the horizontal and vertical position, as well as in the angle (about the trajectory plane normal).
For each regime, we also qualitatively look at the displacement between the initial horizontal fall and a point in time later into the simulation. Based on this displacement, we extrapolate where the leaf would end and compare to @heisinger

#set scale(reflow: true)
#show figure.where(kind: table): set figure.caption(position: top)

#figure(
  grid(
    columns: 3,
    // Creates two auto-sized columns
    gutter: 1em,
    // Adds horizontal space between columns
    // First image with a specific width
    image("assets/image-2.png", width: 90%), image("assets/image.png", width: 90%),
    // Second image with the same width for consistency
    image("assets/image-1.png", width: 90%),
  ),
  caption: [Probability mass vs. x (in) and y (in) positions for discs dropped in fluid with varying parameters. The dimensionless height over diameter for all scenarios are $h slash d approx 19.5$. (A) Image appropriated from Figure 3 in _Coins falling in water_ (2013) by Heisinger et. all. ],
) <heisingers_plot>

#figure(
  table(
    columns: (1fr, 1fr, 1fr, 1fr, 1fr),
    inset: 10pt,
    align: horizon,
    table.header([Scenario], [$I^*$], [$"Re"$], [$t slash d$], [$h slash d space (plus.minus 0.002)$]),
    [A], [$1 times 10^1$], [$5 times 10^3$], [19.5], [19.5],
    [B], [-3], [1.0], [19.5], [19.5],
    [D], [-2], [0.5], [19.5], [19.5],
  ),
  caption: [Parameters for the three scenarioes presented in @heisingers_plot. $I^*$ is the dimensionless moment of inertia. Re is the Reynold's number. $t slash d$ is the dimensionless thickness of disc over diameter of disc. $h slash d$ is the dimensionless height of drop of disc over the diameter of the disc.],
)


= Results

#let process_image_path(path) = {
  block(
    inset: (top: -10em, right: -15em, bottom: 0em, left: -15em),
    clip: true,
    image(
      path,
      width: 90%,
    ),
  )
}

#figure(
  grid(
    columns: 2,
    // Creates two auto-sized columns
    gutter: 1em,
    // Adds horizontal space between columns
    // First image with a specific width
    text([#process_image_path("assets/image-5.png") A (Steady) ]),
    text([#process_image_path("assets/image-4.png") B (Periodic Fluttering)]),
    text([#process_image_path("assets/image-3.png") C (Tumbling Low Inertia)]),
    text([#process_image_path("assets/image-6.png") D (Tumbling High Inertia)]),
  ),
  caption: [Trajectory for falling discs of various parameters at an arbitrary drop height and arbitrary physical scale over 15 seconds, visualized in OpenGL. Simulation data for B, C, D provided by @dusek.],
) <my_plots>

= Analysis

From @my_plots(A) we can see in the stable regime, there is little to no change in horizontal displacement over the drop. This is in agreeance with @heisingers_plot(A).

From @my_plots(B) we can that in the fluttering regime, there is a horizontal displacement that oscillates about 0. This is in agreenace with @heisingers_plot(B): reason dictates the trajectory plane can be rotated at an arbitrary angle about the axis of gravity due to minor perturbations of the initial leaf drop. 

From @my_plots(C) we can see that there is a more complex range of velocities, that is still repeating in nature. Large vertical displacements with little horizontal displacement are followed by smaller vertical drops with a relatively large horizontal displacement in a repeating fashion, a demonstration of periodic vertical and horizontal velocity. Additionally, comparing the starting position of the leaf with the ending position of the leaf, we see that there is a large change in horizontal displacement over the trajectory of the leaf. This is in agreeance with @heisingers_plot(D), where the probability density of a disc's ending position in the tumbling regime is concentrated at large radial displacements.

Finally, from @my_plots(D), which uses data from a higher dimensionless mass disc, we see that there is little to no variation in horizontal and vertical velocity. However, we clearly see that the the angular velocity of the leaf in the trajectory plane is periodic in nature, to a very sinusoidal extent. The end horizontal displacement at $t approx 15"s"$ is also large, which is in agreeance with @heisingers_plot(D).

= Discussion

- Wind itself has varying characteristics. Different temperatures can significantly affect the density of the air (citation needed). The velocity of wind, and local area turbulence may affect both the energy in the air are often non-quasi-static forces, meaning different parts of the air may have different pressures. This means the momentary density of air may not be constant.
- Very surprising. An initial hypothesis was that a rigid body simulation would not be able to fully capture the dynamic behavior of a leaf, because it would lose some of the perturbations one would expect in the flexible mechanical structure of a leaf. However, we have seen from literature, from qualitative analysis of our simulation, that rigid body simulations can in fact capture periodicity in fluttering and tumbling. Perhaps this is due to the nature of fluid interactions already being chaotic enough to exacerbate small perturbations in orienation when an object is dropped. Further research on performant but realistic simulation of leaves in games could perhaps focus on rigid-body simulations and forego softbody simulations, which are more complex.
- We did not consider chaotic
- There are intermediate transfer states between states that we did not account for due to complexity. These may be the most dynamic leaf states.
- Current empirical data for discs in fluid mostly assume a net stationary fluid. A big limitation of the predictive model is thus interactivity with the environment and wind. Full scale numerical simulations as done by @heisinger are still too expensive, but one question is if perhaps an offline simulation with Navier-Stokes can be done across static wind fields, and the result fed into a neural network. 
- Empirical data is limited by set parameters such as $"Re"$ and $I^*$.
- Use of empirical data + predictive models could be the future of real-time leaf simulation in computer graphics.

= Conclusion

= Acknowledgements

Thanks to Professor Jan Dusek for kindly providing numerical data for the falling motion of discs in fluid. Thanks to Professor Mike Bailey for giving advice on the direction of the thesis and general advice on computer graphics.

#bibliography("bibliography.bib")
