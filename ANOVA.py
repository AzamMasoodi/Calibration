import pandas as pd
import numpy as np
from scipy.stats import f_oneway

# Load data from Excel
excel_file_path = 'C:/Masoodi/test/Ksat.xlsx'
df = pd.read_excel(excel_file_path)
column_names = ['Chow', 'Linear', 'Nepf', 'Feldmann', 'Exp', 'Kadlec', '3param']

# Extract data from DataFrame
groups_data = [df[col] for col in column_names]


# Performing ANOVA
f_statistic, p_value = f_oneway(*groups_data)

print("F-Statistic:", f_statistic)
print("P-value:", p_value)

# Interpretation of results
alpha = 0.05
if p_value < alpha:
    print("Reject null hypothesis (H0): There are significant differences between group means.")
else:
    print("Fail to reject null hypothesis (H0): There are no significant differences between group means.")