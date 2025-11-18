from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def get_result(sim_file):
    """
    Reads the result CSV file ('totalseries.csv'), filters the data based on the first and tenth columns,
    converts the 'Time' column which is an integer, and return the filtered data.

    Returns:
    filtered_df

    """
    df = pd.read_csv(sim_file, usecols=[0, 10], skiprows=1)
    # Convert values in 'Column1' to numeric
    df['Time(min)'] = pd.to_numeric(df['Time(min)'])
    # Filter rows with integer values in the first column
    filtered_df = df[df['Time(min)'].astype(int) == df['Time(min)']]
    # Rename the second column to 'Channels'
    # Rename columns
    filtered_df = filtered_df.rename(
        columns={filtered_df.columns[1]: 'Channels'}
    )
    filtered_df.reset_index(drop=True, inplace=True)
    filtered_df['Channels'] = filtered_df['Channels'].diff().fillna(filtered_df['Channels'])
    #filtered_df['Detachment'] = filtered_df['Detachment'].diff().fillna(filtered_df['Detachment'])
    #filtered_df['Deposition'] = filtered_df['Deposition'].diff().fillna(filtered_df['Deposition'])
    #path_filtered_data=Path(sim_file).parent / 'filtered_data.csv'
    path_filtered_data=Path(namefile)
    print(path_filtered_data)
    filtered_df.to_csv(path_filtered_data, index=False)
    return path_filtered_data  
"""def plot(filtered_df, obs_file):
    """
    Plot the simulation and observation data.

    Args:
        filtered_df (str): Path to the CSV file containing filtered data.
        obs_file (str): Path to the CSV file containing observation data.

    Returns:
        show the plot

    """
    
    df_filt = pd.read_csv(filtered_df)
    df_filt.iloc[:, 0] = df_filt.iloc[:, 0] - 1440  # Subtract 1440 from the first column
    df_obs = pd.read_csv(obs_file)
    # Calculate the values of the hydrograph from the cumulative values
    df_obs['Channels'] = df_obs['Channels'].diff().fillna(df_obs['Channels'])[:-1]
    #df_filt['Channels'] = df_filt['Channels'].diff().fillna(df_filt['Channels'])
    time1, runoff1 = df_filt['Time(min)'], df_filt['Channels']
    time2, runoff2 = df_obs['Time'], df_obs['Channels']
    # Plot the data points as blue and red
    plt.plot(time1, runoff1, 'bo', label='Simulation6')
    plt.plot(time2, runoff2, 'r+', label='Observation')
    plt.xlabel('Time(min)')
    plt.ylabel('Runoff(mm)')
    plt.legend()
    plt.show()

"""


obs_file="C:/Masoodi/case/Part1-1D/location2/obs/obs4.csv"
sim_file="C:/Masoodi/case/Part1-1D/result/res14/res2/run2-Oberle/totalseries.csv"
namefile="C:/Masoodi/case/Part1-1D/result/filtered/res14-run6-o_k_.csv"
filtered_df=get_result(sim_file)
plot(filtered_df, obs_file)
#nse(obs_file,filtered_df)