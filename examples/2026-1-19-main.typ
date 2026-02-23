#import "conf.typ": *
#import "@preview/unify:0.7.1": *

#show: arkheion.with(
  title: "Coaxial Lab HW 5b",
  authors: (
    (name: "Shengdong Li", email: "lishen@oregonstate.edu", affiliation: "Oregon State University"),
  ),
  date: "May 2, 2025",
)

#show ref: it => {
  set text(blue)
  it
}

#set cite(style: "ieee")
#show figure.where(kind: table): set figure.caption(position: top)

// units
#let V = unit("volt")
#let s = unit("second")
#let S = unit("siemens")
#let V_R = $"V"_"R"$
#let V_Ext = $"V"_"Ext"$
#let Hz = unit("hertz")
#let khz = $"k"unit("hertz")$
#let ohm = unit("ohm")

#let w0 = $omega_0$
#let wd = $omega_d$
#let vin = $V_"Ext"$
#let v0 = $V_0$
#let vout = $V_"R"$
#let iss = $I_"ss"$


= Coaxial Cable Circuit Diagram

== Schematic Diagram

#let vapp = $"V"_"app"$
#let vt = $"V"_"T"$
#figure(
  image("circuit.svg"),
  caption: [Representative circuit model of two coaxial cables using lumped-element components. The structure of cascaded resistors, inductors, and capacitors serves to approximate the distributed inductance, resistance and capacitance per length of the first cable. The variable resistor at the end represents the resistance of the second coaxial cable. Two points of voltage are noted, #vapp and #vt],
) <circuit>

== Added Caption

(See caption attached to @circuit)

== Short Paragraph Describing Lab

In this lab, the voltage over time graph of an applied pulse at #vapp (see @circuit) was measured via oscilloscope, over the timeframe encompassing the two events. One, right before a voltage pulse is about to be sent out from the A/C voltage source, and two, right after the wavefront of the voltage pulse interacts with the boundary of the first coaxial cable with the second coaxial cable, reflects over the boundary, and reaches #vapp once again. This time dependence on voltage was measured with various terminating resistors of different resistance. Additionally, the voltage over time #vt was also measured (see @circuit) in between these two events.

= Speed of Wave Propagation in a Cable

== Method of Speed Calculation

$
  "(upload image from phone)"
$ <wavepic>

Using the voltage over time graph of an applied pulse at #vapp, the driving force and frequency of the input voltage and scale of the oscilloscope was changed until two clear waveforms were visible on the oscilloscope: one curve (left in @wavepic) represents the initial voltage pulse sent out from the A/C power source, and the second curve (right in @wavepic) represents the second voltage curve.

The time delta $Delta t$ was taken between the measurement of the time when the input pulse was fully sent out, and the time it took to record a second peak in the rebound pulse of th wavefront.

Since the coaxial cable was 150 m long, and the electromagnetic fields carrying energy from the pulse at the left end of the coaxial cable must go from one end of the coaxial cable to the other, bounce, and come back towards the source, the speed of light was taken to be

$
  v = d / (Delta t) = (150 "m") / (Delta t)
$

== Calculated Speed of light

$Delta t$ was measured to be $1.52mu "s"$, so the speed of light was calculated to be $approx 1.97times 10^8 "m" / "s" approx 0.66 "c"$.

== Electron vs. Photon Speed

The drift velocity of electrons in the material was not measured at all, so from a purely empirical viewpoint, it is unsure how the speed of electron drift compares to that from the photon speed. However,

- Coaxial cable was measured to have a resistance of $12.4 #ohm$
- $I = V / R = (2.2#V) / (12.4 #ohm) approx 0.18 "A"$
- $I = (d Q) / (d t) = v_d A e n -> v_d = I / (A e n)$
where $v_d$ is the drift velocity, $A$ is the cross-sectional area of a segment of wire, $e$ is the charge of an electron ($1.6 times 10^(-19) "C"$), and $n$ is the free electron density.
- the coaxial cable was measured to be roughly $5"mm"=5times 10^(-3) "m"$ in diamater, and the free electron density of copper is roughly $8.4times 10^(28) "m"^(-3)$
$v_d = I / (pi (D / 2)^2 e n) approx .68 (mu "m") / "s"$, which is incredibly small, a 15 order of magnitude difference between this speed and the speed of light. Therefore, the electrons in the wire are travelling at nowhere near the speed of propagation of light. It is likely that the propagation of electric and magnetic waves are what are pushing electrons along the coaxial cable, and not the couloumb force of one free electron interacting with another.

= Coaxial Cable Lab: Data Table
== Data Tables
// #bibliography("bibliography.bib", style: "ieee")
