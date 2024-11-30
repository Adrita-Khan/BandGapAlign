# -*- coding: utf-8 -*-
"""band_gap_prediction_preprocessing

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1rB8WVT6JSUPb0Behi51R6A-AiEVfEW0r

This work utilizes code from the **IntroMLLab** and **MAST-ML** modules available on NanoHub, as detailed below:

1. **Machine Learning Lab Module (IntroMLLab):**  
   [IntroMLLab on NanoHub](https://www.nanohub.org/resources/intromllab)

2. **Materials Simulation Toolkit for Machine Learning (MAST-ML):**  
   - [MAST-ML on NanoHub](https://www.nanohub.org/resources/mastmltutorial)  
   - [MAST-ML GitHub Repository](https://github.com/uw-cmg/MAST-ML)

In this work, we specifically import modules from **MAST-ML** to support our development.
"""

pip install mastml pymatgen scikit-lego linear-tree gplearn cbfv deepchem duecredit

# MAST-ML imports for machine learning and feature engineering
from mastml.mastml import Mastml
from mastml.models import SklearnModel
from mastml.preprocessing import SklearnPreprocessor
from mastml.feature_selectors import SklearnFeatureSelector, EnsembleModelFeatureSelector
from mastml.data_splitters import SklearnDataSplitter  # Additional options: NoSplit, LeaveOutPercent
from mastml.feature_generators import ElementalFeatureGenerator  # Additional option: OneHotGroupGenerator
from mastml.hyper_opt import GridSearchCV  # Additional options: GridSearch, RandomizedSearch, BayesianSearch
from mastml.metrics import Metrics

# Standard library imports for data manipulation and time tracking
import os
import time
import random
from copy import copy
from collections import Counter

# Third-party library imports for data analysis and visualization
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import sklearn.utils
from sklearn import tree
from sklearn.model_selection import KFold, RepeatedKFold, train_test_split
import pymatgen

# Set random seed for reproducibility
seed = 12345123
np.random.seed(seed)
sklearn.utils.check_random_state(seed)

# Raw URL of the dataset
data_url = 'https://raw.githubusercontent.com/Adrita-Khan/BandGapAlign/main/data/citrination-export.csv'
mastml_df = pd.read_csv(data_url)  # Read dataset from the URL
mastml_df  # Display the dataframe

# Filter unnecessary or irrelevant columns and rows from the dataframe

# Drop the 'Color' column from the dataframe
mastml_df_filtered = mastml_df.drop(columns=['Color'])

# Uncomment one of the following lines to filter rows based on 'Crystallinity':
# Retain only rows where 'Crystallinity' is 'Single crystalline'
# mastml_df_filtered = mastml_df_filtered[mastml_df_filtered["Crystallinity"] == 'Single crystalline']

# Retain only rows where 'Crystallinity' is 'Polycrystalline'
# mastml_df_filtered = mastml_df_filtered[mastml_df_filtered["Crystallinity"] == 'Polycrystalline']

# Display the filtered dataframe
mastml_df_filtered

# Convert 'Band gap' column to numeric, coercing errors to NaN to exclude rows with invalid values (e.g., containing ± sign)
mastml_df_filtered['Band gap'] = pd.to_numeric(mastml_df_filtered['Band gap'], errors='coerce')

# Optional: Uncomment the following line to explicitly handle rows with ± sign
# mastml_df_filtered = mastml_df_filtered.drop('Band gap', axis=1).join(
#     mastml_df_filtered['Band gap'].apply(pd.to_numeric, errors='coerce')
# )

# Clean 'Chemical formula' column by removing special characters (e.g., subscripts, superscripts, etc.)
mastml_df_filtered['Chemical formula'] = mastml_df_filtered['Chemical formula'].str.replace(r'[$_{}]', '', regex=True)

# Drop rows with missing (NaN) values across the dataframe
mastml_df_filtered = mastml_df_filtered.dropna()

# Display the cleaned dataframe
mastml_df_filtered

# Filter and display rows where 'Band gap' contains NaN values (e.g., due to invalid entries like ± sign)
formulas_with_invalid_band_gap = mastml_df_filtered[mastml_df_filtered['Band gap'].isna()]

# Display the chemical formulas with invalid 'Band gap' entries
formulas_with_invalid_band_gap

# Remove any rows with NaN values, ensuring all formerly invalid entries (e.g., from regex or conversions) are excluded
mastml_df_clean = mastml_df_filtered.dropna()

# Display the cleaned dataframe
mastml_df_clean

# Options for filtering rows based on the 'Band gap' range
# Uncomment one or both of the following lines as needed:

# Remove rows where 'Band gap' is greater than 5.0
# mastml_df_clean = mastml_df_clean[mastml_df_clean['Band gap'] <= 5.0]

# Remove rows where 'Band gap' is less than 0.2
# mastml_df_clean = mastml_df_clean[mastml_df_clean['Band gap'] >= 0.2]

# Identify and list recurring compounds based on 'Chemical formula'
reoccurring_compounds = (
    mastml_df.groupby('Chemical formula')  # Group by 'Chemical formula'
    .filter(lambda group: len(group) > 1)  # Keep groups with more than one entry
    .drop_duplicates(subset=['Chemical formula', 'Band gap'], keep='first')  # Remove duplicate entries
    .sort_values(by='Chemical formula')  # Sort by 'Chemical formula'
)

# Display the resulting dataframe of recurring compounds
reoccurring_compounds

# Display column names in the DataFrame
print("Column names in the DataFrame:")
print(mastml_df_clean.columns)

# Remove any leading or trailing spaces from column names
mastml_df_clean.columns = mastml_df_clean.columns.str.strip()

# Check for the exact column name and calculate statistics for 'Band gap'
if "Band gap" in mastml_df_clean.columns:
    stats = mastml_df_clean["Band gap"].describe().round(3)
    print("Statistics for 'Band gap':")
    print(stats)
elif "Band Gap" in mastml_df_clean.columns:
    stats = mastml_df_clean["Band Gap"].describe().round(3)
    print("Statistics for 'Band Gap':")
    print(stats)
else:
    print("The column 'Band gap' or 'Band Gap' does not exist in the DataFrame.")

# Statistics for the band gap values in the data set
mastml_df_clean["Band gap"].describe().round(3)

import matplotlib.pyplot as plt
import numpy as np

def histogram_plot(data, bins_range=(0, 14), bin_width=1, color='orange', edge_color='black', title='Band Gap Distribution', xlabel='Band gap (eV)', ylabel='Count', figsize=(9, 4), dpi=400):
    """
    Plots a histogram for the provided data with customizable options.

    Parameters:
        data (pd.Series or array-like): Data to be plotted in the histogram.
        bins_range (tuple): Range for the histogram bins (default: (0, 14)).
        bin_width (int or float): Width of each bin (default: 1).
        color (str): Color of the bars (default: 'orange').
        edge_color (str): Color of the bar edges (default: 'black').
        title (str): Title of the plot (default: 'Band Gap Distribution').
        xlabel (str): Label for the x-axis (default: 'Band gap (eV)').
        ylabel (str): Label for the y-axis (default: 'Count').
        figsize (tuple): Figure size (default: (9, 4)).
        dpi (int): Dots per inch for the figure (default: 400).
    """

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Plot the histogram
    ax.hist(data, bins=np.arange(bins_range[0], bins_range[1] + bin_width, bin_width), density=True, color=color, edgecolor=edge_color, lw=1)

    # Set axis labels and title
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14)

    # Set x and y ticks based on the data range
    ax.set_xticks(np.arange(bins_range[0], bins_range[1] + bin_width, bin_width))
    ax.set_yticks(np.arange(0, ax.get_ylim()[1], 0.1))  # Dynamic y-ticks based on data

    # Show the plot
    plt.show()

# Example usage: Plot histogram of 'Band gap' column from a DataFrame
histogram_plot(mastml_df_filtered["Band gap"].astype("float"))

# Display unique 'Chemical formula' values in the cleaned DataFrame
unique_chemical_formulas = mastml_df_clean["Chemical formula"].unique()

# Print the unique chemical formulas
print("Unique Chemical Formulas:")
print(unique_chemical_formulas)

# Optionally, print the total count of unique formulas
print(f"Total unique chemical formulas: {len(unique_chemical_formulas)}")

import re
from pymatgen.core.composition import Composition

# Function to clean chemical formulas
def clean_chemical_formula(formula):
    """
    Cleans the chemical formula by:
    - Replacing LaTeX-like subscript formatting ($_{}) with numeric subscripts.
    - Converting fractional compositions into a format parsable by pymatgen.
    """
    # Replace LaTeX-like subscript formatting ($_{...}$) with numeric subscripts
    cleaned_formula = re.sub(r'\$_\{([0-9.]+)\}\$', r'\1', formula)

    # Replace fractional subscripts in specific cases (e.g., Bi$_{0.85}$Sb$_{0.15}$ -> Bi0.85Sb0.15)
    cleaned_formula = re.sub(r'([A-Za-z]+)\$_\{([0-9.]+)\}\$', r'\1\2', cleaned_formula)
    return cleaned_formula

# Clean the "Chemical formula" column
mastml_df_clean["Chemical formula"] = mastml_df_clean["Chemical formula"].apply(clean_chemical_formula)

# Verify the cleaned formulas
print("Cleaned Chemical Formulas:")
print(mastml_df_clean["Chemical formula"].unique())

# Parse out individual elements using pymatgen's Composition parser
element_list = []
failed_formulas = []

for idx in mastml_df_clean.index:
    formula = mastml_df_clean.loc[idx, "Chemical formula"]
    try:
        # Parse the formula with pymatgen's Composition
        composition = Composition(formula)
        element_list.extend(composition.elements)  # Add elements to the list
    except Exception as e:
        # Log failed formulas for further inspection
        print(f"Failed to parse formula: {formula}, Error: {e}")
        failed_formulas.append(formula)

# Display the parsed elements
print("Parsed Elements:")
print(set(element_list))

# Display formulas that could not be parsed
if failed_formulas:
    print("\nFormulas that failed to parse:")
    print(failed_formulas)

def clean_and_parse_formula(formula):
    # Replace LaTeX-like subscript formatting with numeric subscripts
    formula = re.sub(r'\$_\{([0-9.]+)\}\$', r'\1', formula)

    # Handle fractional formulas, e.g., Bi0.85Sb0.15
    try:
        composition = Composition(formula)
        return composition.elements  # Return parsed elements
    except Exception as e:
        print(f"Failed to parse formula: {formula}, Error: {e}")
        return None  # Return None for invalid formulas

# Clean and parse formulas
parsed_elements = []
for idx, formula in enumerate(mastml_df_clean["Chemical formula"]):
    elements = clean_and_parse_formula(formula)
    if elements:
        parsed_elements.extend(elements)

# Unique parsed elements
print("Parsed Elements:")
print(set(parsed_elements))

# setup a counter to count each element
temp_counter = Counter(element_list)
element_tuples = list(zip(list(temp_counter.keys()),list(temp_counter.values())))
element_df = pd.DataFrame(element_tuples,columns=["Element","Count"])
element_df_sorted = element_df.sort_values(by=["Count"],ascending=False)

element_df_sorted

data = mastml_df_clean['Chemical formula']
target = mastml_df_clean['Band gap']

feature_types = ['composition_avg','max', 'min', 'difference']
#feature_types = ['composition_avg', 'arithmetic_avg']
#feature_types = ['difference','max', 'min']
#feature_types = ['composition_avg']