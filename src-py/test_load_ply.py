import pygltflib
import numpy as np
import os
from plyfile import PlyData, PlyElement
import matplotlib.pyplot as plt

def load_ply(ply_path: str) -> tuple[int, int, int, int]:
    # a = np.array([1, 2, 3])
    # b = np.array([4, 5, 6])
    # c = np.array([7, 8, 9])
    # print(c.shape)#(3,1)
    # #i want (3,3)
    # res = np.stack((a, b, c), axis=1)
    # print(res)
    # print(res.shape)

    # a = np.array([1, 2, 3])
    # b = np.array([4, 5, 6])
    # rr = np.stack((a, b))
    # print(rr)
    # print(rr.shape)

    with open(ply_path, 'rb') as f:
        plydata = PlyData.read(f)
        
        points = np.stack(
            (
                plydata['vertex']['x'],
                plydata['vertex']['y'],
                plydata['vertex']['z']
            ),
            axis=1
        )
        print(points)

        l = -2
        r = 2
        x = np.linspace(l, r, 1000)   
        y = np.linspace(l, r, 1000)        
        z = np.linspace(l, r, 1000)        

        #X,Y,Z = np.meshgrid(x, y, z)
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')

        ax.scatter(plydata['vertex']['x'], plydata['vertex']['y'], plydata['vertex']['z'])
        plt.show()





load_ply(os.path.abspath('art/elm_point_cloud.ply'))