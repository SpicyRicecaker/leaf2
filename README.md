# data statement

The data for falling leaves is kindly provided by Prof. Jan Dusek, published in the research paper "Numerical Simulation of the Dynamics of Freely Falling Discs" (2013). I do not take credit for any of the highly detailed data, nor the insights provided by his and his colleagues in the paper. 

# todo

- Read in matplot data into dataframe
- Determine velocity at the start of the current frame via a binary search over the time
- Lerp between the two endpoints of the interval to find velocity
- Multiply the velocity by the change in time of the frame to find displacement in
    - Translational x
    - Translational z
    - Rotational angle

for now let's just not think about the frame and scrubback