# todo

- Read in matplot data into dataframe
- Determine velocity at the start of the current frame via a binary search over the time
- Lerp between the two endpoints of the interval to find velocity
- Multiply the velocity by the change in time of the frame to find displacement in
    - Translational x
    - Translational z
    - Rotational angle

for now let's just not think about the frame and scrubback