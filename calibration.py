import os
import rasterio
import csv
import pandas as pd
import numpy as np

""" _________Filtering output data________"""
# Specify the input CSV file path
sim_file = 'totalseries.csv'
# Specify the observation CSV file path
obs_file='observation.csv'
# Specify the filtered CSV file path
output_file='filtered_data.csv'
def filterdata(sim_file):
    """
    Reads a CSV file ('totalseries.csv'), filters the data based on the first and tenth columns,
    converts the 'Time' column which is integer, and saves the filtered data to a new CSV file ('filtered_data.csv').

    Returns:
    filtered_df

    """
    df = pd.read_csv(sim_file, usecols=[0, 10], skiprows=1) 
    df['Time'] = pd.to_numeric(df['Time'])  # Convert values in 'Column1' to numeric
    filtered_df= df[df['Time'].astype(int) == df['Time']]  # Filter rows with integer values in first column
    filtered_df.to_csv('filtered_data.csv', index=False)
    return filtered_df


""" _________Calculate NSE_________"""
def nse(obs_file):
    """
    Calculates the Nash-Sutcliffe Efficiency (NSE) using observation and simulation data from CSV files.
    Args:
        sim_file (str): Path to the simulation CSV file.

    Returns:
        float: Nash-Sutcliffe Efficiency (NSE) value.

    """

    
    obs_df = pd.read_csv(obs_file)
    output_df = pd.read_csv(output_file)
    

    # Calculate the Nash-Sutcliffe Efficiency
    nse = 1 - np.sum((output_df.Channels - obs_df.Channels) ** 2) / np.sum((obs_df.Channels - obs_df.Channels.mean()) ** 2)
    bias = output_df.Channels.mean() - obs_df.Channels.mean()

    print('Nash-Sutcliffe Efficiency:', nse)
    return nse, bias

""" _________Run LISEM_________"""
def open_lisem(k):
    """
    Opens a raster file, replaces cell values with 'k' value, changes directory to the LISFLOOD-FP executable path,
    and runs the LISFLOOD-FP model.

    Args:
        k (float): Value of 'k' to replace cell values in the raster.

    Returns:
        totalseries.csv

    """
    #Open ksat raster
    ksat_file = rasterio.open("C:/Masoodi/case/Reis2020/Model/Maps/ksat1.map")
    ksat = ksat_file.read(1)
    # Replace cell value with k value
    ksat[:, :] = k
    # Change directory to the lisem path
    os.chdir(lisem_path)
    # Run lisem with the run file
    os.system(f"{lisem_path} -r {run_path}")
    
def run_k(k):
    """
    Runs lisem with a specific k value and returns the nse and bias of that run


    Returns
    -------
    nse, bias (float)

    """
    open_lisem(k)
    # 
    filterdata(sim_file)
    return nse(obs_file)[0]  # Calculate nse function for each 'k'
    
""" _________optimal_k_________"""
def opt_k(min_k, max_k, num_steps=10):
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
    while nse(obs_file)[0]<0.8:
        step = (max_k - min_k) / (num_steps - 1)  # Calculate the step size
        k_values = [min_k + step * i for i in range(num_steps)]  # Generate the 'k' values
        results = []
        for run_no, result in enumerate(map(run_k, k_values)):
            results.append(result)
            print(f'round = {round}, run = {run_no}/{num_steps}, k = {k_values[run_no]}')
        max_result = max(results)  # Find the maximum value in the 'results' list
        max_index = results.index(max_result)  # Find the index of the maximum value
        k_opt = k_values[max_index]  # Get the corresponding 'k' value 
        min_k= k_opt-step
        max_k= k_opt+step
        round += 1
    print("Maximum value:", max_result)
    print("Value produced by k:", k_opt) 
    return k_opt

if __name__ == '__main__':
    # Path to the executable file
    lisem_path ="C:/Masoodi/lisem/lisemv6873/Lisem.exe"
    run_path = "C:/Masoodi/case/Reis2020/Model/run/run1.run"
    opt_k(8, 100, num_steps=10)           
        

    
    TODO = """
    - AM: Check everything is running
    - AM: Add code to change simfile and output for each k in runfile
    - PK: Add multiprocessing code
    - PK: find a way to run lisem headless. Check out xvfb, like here: https://askubuntu.com/a/1111898
    """

 