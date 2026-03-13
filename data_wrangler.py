import h5py
import pandas as pd
import numpy as np
import os
import scipy.io as sio
import unittest

def lerp(t0, t1, a, b, t):
    interval = t1 - t0
    progress = (t - t0) / interval

    out = a + (b - a) * progress
    return out

class DiscTransformPredictor:
    def __init__(self, path, frametime):
        self.path = path
        self.df = None
        
        try:
            mat_dict = sio.loadmat(path)
            data_dict = {k: v for k, v in mat_dict.items() if not k.startswith('__')}
            
            for key, value in data_dict.items():
                if isinstance(value, np.ndarray):
                    data_dict[key] = np.squeeze(value)
            
            self.df = pd.DataFrame(data_dict)

            match path:
                case "data_m01_G90.mat":
                    self.df.t -= 2.478290000000000e+02 # zero out the time
            
        except NotImplementedError:
            print("Error: This appears to be a MATLAB v7.3+ file. Use 'h5py' instead.")
        except Exception as e:
            print(f"An error occurred while loading the file: {e}")
        
        # populate the basecase
        self.xs = [0]
        self.zs = [10] # this will probably change later
        self.phis = [0]
        self.n_i = 1
        self.frametime = frametime
        self.steps_per_frametime = 10

    def t(self, i):
        return i * self.frametime
    
    def integrate_column(self, column, t0, t1, n):
        dt = (t1 - t0) / n
        t_current = t0

        acc = 0
        for _ in range(n):
            # todo, can use a better verlet algorithm here.
            acc += self.column_at_t(t_current, column) * dt
            t_current += dt
        
        return acc

    def x(self, i):
        if i < self.n_i:
            return self.xs[i]
        if i >= self.n_i:
            res = self.x(i - 1) + self.integrate_column('ux', self.t(i - 1), self.t(i), self.steps_per_frametime)
            self.xs.append(res)
            self.n_i += 1
            return res
        
    def column_at_t(self, t, column):
        # print(self, t, column)
        # print(self.df)
        # print(self.df['t'])
        length = len(self.df['t'])
        assert length >= 2, "Lazy algorithm 2 or greater length"
        i_L = 0
        i_R = length - 1 - 1

        i_interval_begin = -999
        i_interval_end = -999

        i_debug_count = 0
        while i_L != i_R:
            i_debug_count += 1
            if i_debug_count % 100 == 0:
                print(f'still binary searching jumps: {i_debug_count}, i_L: {i_L}, i_R: {i_R}')
            i_test = i_L + (i_R - i_L) // 2
            if t >= self.df['t'][i_test] and t <= self.df['t'][i_test + 1]:
                i_interval_begin = i_test
                i_interval_end = i_test + 1
                break
            # if we are to the right of the interval
            if t > self.df['t'][i_test + 1]:
                i_L = i_test + 1
                continue
            # if we are to the left of the interval
            if t < self.df['t'][i_test]:
                i_R = i_test
                continue
        
        assert not (i_interval_begin == -999), f"Big error occurred: no matching interval for given t {t}"
        
        res = lerp(self.df['t'][i_interval_begin], self.df['t'][i_interval_end], self.df[column][i_interval_begin], self.df[column][i_interval_end], t)
        return res


# ==========================================
#               TEST SUITE
# ==========================================
class TestFileReader(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """This runs ONCE before any tests start. We use it to create a mock .mat file."""
        cls.test_filepath = "test_data.mat"
        mock_data = {
            't': np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5]),
            'sensor_x': np.array([[10], [12], [11], [15], [14], [13]]), # MATLAB 2D column
            'ux': np.array([1, 2, 3, 4, 5, 6])                    # Standard 1D array
        }
        sio.savemat(cls.test_filepath, mock_data)

    @classmethod
    def tearDownClass(cls):
        """This runs ONCE after all tests complete. We use it to clean up the file."""
        if os.path.exists(cls.test_filepath):
            os.remove(cls.test_filepath)

    def test_dataframe_creation_and_print(self):
        """Test that the DataFrame loads and print it to the console."""
        reader = DiscTransformPredictor(self.test_filepath)
        
        # Check that it actually created a DataFrame
        self.assertIsNotNone(reader.df, "DataFrame failed to load and is None")
        self.assertIsInstance(reader.df, pd.DataFrame, "df is not a pandas DataFrame")
        
        # Explicitly printing it as requested
        print("\n--- DataFrame Loaded in Test ---")
        print(reader.df)
        print("--------------------------------\n")

    def test_data_shape_and_squeezing(self):
        """Test that MATLAB's (N,1) arrays are properly flattened to (N,) for Pandas."""
        reader = DiscTransformPredictor(self.test_filepath)

        # Verify columns exist
        expected_columns = ['time', 'sensor_x', 'sensor_y']
        self.assertListEqual(list(reader.df.columns), expected_columns)
        
        # Verify the length
        self.assertEqual(len(reader.df), 6, "DataFrame should have exactly 6 rows")
        
        # Verify the 2D array was squeezed into a 1D Pandas Series correctly
        self.assertEqual(reader.df['sensor_x'].shape, (6,), "sensor_x was not squeezed properly")
        self.assertEqual(reader.df['sensor_x'].iloc[0], 10, "First value of sensor_x should be 10")

    def test_invalid_file_handling(self):
        """Test how the class handles a missing file."""
        reader = DiscTransformPredictor("some_non_existent_file.mat")
        
        # Based on our current __init__, if it fails, df remains None
        self.assertIsNone(reader.df, "df should remain None if file is not found")
    
    def test_integrator(self):
        reader = DiscTransformPredictor(self.test_filepath)
        res = reader.x(6)
        # print(reader.xs)
        self.assertAlmostEqual(res, 0.14916666666666667)

    def test_intervals(self):
        reader = DiscTransformPredictor(self.test_filepath)

        self.assertAlmostEqual(reader.column_at_t(0.05, 'ux'), 1.5)

    def test_i_can_read_data(self):
        reader = DiscTransformPredictor("data_m01_G90.mat")
        import matplotlib.pyplot as py
        py.plot(reader.df['t'], reader.df['ux'])
        py.show()

if __name__ == '__main__':
    import unittest
    # Running this will execute all functions starting with 'test_'
    # unittest.main(verbosity=2)
    suite = unittest.TestSuite()
    suite.addTest(TestFileReader("test_intervals"))
    suite.addTest(TestFileReader("test_integrator"))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


