import os
import rasterio
import csv
import pandas as pd
import numpy as np
import re


class LisemKOptimizer:
    def __init__(self, run_file, obs_file, lisem_path):
        self.run_file = run_file
        self.obs_file = obs_file
        # self.output_file = output_file
        self.lisem_path = lisem_path

    def opt_k(self, min_k, max_k, num_steps):
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
            results.append(self.run_k(k))
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
        self.open_lisem(k)
        output_df = self.filterdata()

        return self.nse(obs_file, output_df)[0]

    def get_value_from_runfile(self, variablename):
        """
        Gets a value from the runfile
        """
        runfile = open(self.run_file).read()
        m = re.search(variablename + '=(.*)', runfile)
        if not m:
            raise ValueError(
                f'{variablename} not in lisem runfile {self.run_file}')
        return m.group(1)

    def open_lisem(self, k):
        """
        Opens a raster file, replaces cell values with 'k' value,
        and runs the LISEM model.

        Args:
            k (float): Value of 'k' to replace cell values in the raster.

        Returns:
            totalseries.csv

        """
        # Open ksat raster - can't be an absolute path. Change to relative path with variable name
        map_dir = self.get_value_from_runfile('Map Directory')
        ksat_file = rasterio.open(map_dir + "/ksat1.map", "r+")
        ksat = ksat_file.read(1)
        # Replace cell value with k value
        ksat[:, :] = k
        # Save the modified data back to the raster file
        ksat_file.write(ksat, 1)
        ksat_file.close()  # Close the raster file
        # Run lisem with the run file
        os.system(f"{lisem_path} -r {run_path}")

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
        print('Nash-Sutcliffe Efficiency:', nse)
        return nse, bias

    def filterdata(self):
        """
        Reads a CSV file ('totalseries.csv'), filters the data based on the first and tenth columns,
        converts the 'Time' column which is an integer, and saves the filtered data to a new CSV file ('filtered_data.csv').

        Returns:
        filtered_df

        """
        sim_file = self.get_value_from_runfile(
            'Result Directory') + '/totalseries.csv'
        df = pd.read_csv(sim_file, usecols=[0, 10], skiprows=1)
        # Convert values in 'Column1' to numeric
        df['Time(min)'] = pd.to_numeric(df['Time(min)'])
        # Filter rows with integer values in the first column
        filtered_df = df[df['Time(min)'].astype(int) == df['Time(min)']]
        # Rename the second column to 'Channels'
        filtered_df = filtered_df.rename(
            columns={filtered_df.columns[1]: 'Channels'})
        filtered_df.reset_index(drop=True, inplace=True)
        return filtered_df


if __name__ == '__main__':
    # Path to the executable file
    lisem_path = "C:/Masoodi/lisem/lisemv6873/Lisem.exe"
    run_path = "C:/Masoodi/test/run1/run6.run"
    k_path = "C:/Masoodi/test/map1/ksat1.map"
    sim_file = 'C:/Masoodi/test/res1/totalseries.csv'
    # Specify the observation CSV file path
    obs_file = 'C:/Masoodi/test/obs1/obs6.csv'
    opt = LisemKOptimizer(run_path, obs_file, lisem_path)
    opt.opt_k(2, 20, 5)
