import sys
import os
import pandas as pd
import numpy as np
from lisemrunner import LisemRunner

class LisemKOptimizer:

    def __init__(self, lisemrunner:LisemRunner,  obs_file):
        self.runner = lisemrunner
        self.runner_base_name = self.runner.name
        self.obs_file = obs_file

    def regulaFalsi_k(self, min_k, max_k, epsilon, num_steps: int):
        """
        Implements regula Falsi method to find the optimal 'k' value by iterating through a range of 'k' values.
        Calls the open_lisem, filterdata, and nse functions(Bias).

        Args:
            min_k (float): Minimum value of 'k' to start the iteration.
            max_k (float): Maximum value of 'k' to end the iteration.
            num_steps (int, optional): Number of steps within the range of 'k' values.

        Returns:
            float: Optimal 'k' value.

        """
        round=0
        f_min_k = self.run_k(min_k)[1]
        f_max_k = self.run_k(max_k)[1]
        if f_min_k * f_max_k >= 0: 
            print("You have not assumed right a and b") 
            return -1
        c = min_k # Initialize result 
          
        for i in range(num_steps): 
            round += 1
            # Find the point that touches x-axis 
            c = (min_k * f_max_k - max_k * f_min_k)/ (f_max_k - f_min_k) 
            f_opt_k = self.run_k(c)[1] 
            print(
                 f'round = {round}, k = {c}, bias={f_opt_k}') 
            # Check if the above found point is the root 
            if abs(f_opt_k) < epsilon:
                break
            
            # Decide the side to repeat the steps 
            elif (f_opt_k  * f_min_k) < 0: 
                max_k = c 
                f_max_k = f_opt_k
            else: 
                min_k = c 
                f_min_k = f_opt_k
        print("The value of k_opt is : " , '%.4f' %c)
        
    def opt_k(self, min_k, max_k, num_steps: int):
        """
        Implements the Try and Error method to find the optimal 'k' value by iterating through a range of 'k' values.
        Calls the open_lisem, filterdata, and nse functions.

        Args:
            min_k (float): Minimum value of 'k' to start the iteration.
            max_k (float): Maximum value of 'k' to end the iteration.
            num_steps (int, optional): Number of steps within the range of 'k' values. Defaults to 10.

        Returns:
            float: Optimal 'k' value.

        """
        round = 0
        max_result = 0.0
        k_opt = None
        while True:
            step = (max_k - min_k) / (num_steps - 1)  # Calculate the step size
            # Generate the 'k' values
            k_values = [min_k + step * i for i in range(num_steps)]
            #k_values  = np.random.uniform(min_k, max_k, size = num_steps)
            results = self.run_opt_round(k_values, round)
            # Find the maximum value in the 'results' list
            max_result = max(results)
            # Find the index of the maximum value
            max_index = results.index(max_result)
            k_opt = k_values[max_index]  # Get the corresponding 'k' value
            if max_result > 0.8 or round > 10:
                break
            min_k = k_opt-step
            max_k = k_opt+step
            round += 1
        print("Maximum value:", max_result)
        print("Value produced by k:", k_opt)
        return k_opt

    def run_opt_round(self, k_values: list, round_no: int):
        results = []
        for run_no, k in enumerate(k_values):
            results.append(self.run_k(k)[0])
            print(
                f'round = {round_no}, run = {run_no}/{len(k_values)}, k = {k_values[run_no]}')
        return results
        
 
    def run_k(self, k):
        """
        Runs lisem with a specific k value and returns the nse and bias of that run


        Returns
        -------
        nse, bias (float)

        """
        self.runner.name = self.runner_base_name + f'_k_{k:0.4f}'
        output_df = self.runner.run(ksat=k)
        return self.nse(obs_file, output_df)


    def nse(self, obs_file, output_df):
        """
        Calculates the Nash-Sutcliffe Efficiency (NSE) using observation and simulation data from CSV files.
        Parameters:
            obs_file (str): Path to the observation CSV file.
            output_df (pd.DataFrame): A dataframe containing the simulation result, as prepared by filterdata

        Returns:
            float: Nash-Sutcliffe Efficiency (NSE) value.

        """

        obs_df = pd.read_csv(self.obs_file)
        # Calculate the Nash-Sutcliffe Efficiency
        nse = 1 - (np.sum((output_df.Channels - obs_df.Channels) ** 2)) / \
            (np.sum((obs_df.Channels - obs_df.Channels.mean()) ** 2))
        bias = output_df.Channels.mean() - obs_df.Channels.mean()
        print('Nash-Sutcliffe Efficiency:', nse, ' Bias: ', bias)
        return nse, bias

if __name__ == '__main__':
    # Path to the executable file
    if len(sys.argv) < 4:
        sys.stderr.write('Usage: python calibration.py <lisem_path> <runfile> <observation_file>')
    lisem_path, run_path, obs_file = sys.argv[1:4]
    lr = LisemRunner(lisem_path, run_path, os.path.basename(run_path).replace('.run', '-c'))
    lr.result_path = lr.path.parent.absolute() / 'res'
    lr['map_dir'] = (lr.path.parent / 'map').absolute().as_posix() + '/'
    print(lr.name, ':', lr.path, lr.result_path, lr.runfilename(), lr['map_dir'])
    lr.save()
    opt = LisemKOptimizer(lr, obs_file)
    opt.opt_k(5, 15, 5)
    #opt.regulaFalsi_k(5.0, 15.0, 0.01, 5)
