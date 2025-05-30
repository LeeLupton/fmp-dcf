![Python](https://img.shields.io/badge/Python-3.x-blue)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-lightblue)
![Requests](https://img.shields.io/badge/Requests-library-orange)
![Pandas](https://img.shields.io/badge/Pandas-data%20analysis-red)
![tksheet](https://img.shields.io/badge/tksheet-table%20widget-purple)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
# Custom DCF Application

## Description

This is a Python application built with Tkinter and tksheet for performing custom discounted cash flow (DCF) analysis. It fetches financial data using the Financial Modeling Prep API and displays it in an interactive, Excel-like table. The application also includes features for choosing visible columns, creating pivot tables, and exporting data to JSON.

## Prerequisites

*   Python 3.6 or higher
*   pip (Python package installer)

## Setup

1.  **Clone the repository (if applicable):**
    ```bash
    # If the code is in a repository, provide clone instructions here.
    # Example: git clone <repository_url>
    # cd <repository_directory>
    ```
    Since the code was provided directly, ensure you are in the directory containing `dcf.py`, `.env`, and `requirements.txt`.

2.  **Install dependencies:**
    Navigate to the project directory in your terminal and run:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up the environment file:**
    Create a file named `.env` in the project directory.
    If you have an FMP API key, add it to this file in the following format:
    ```
    FMP_API_KEY="YOUR_API_KEY_HERE"
    ```
    Replace `"YOUR_API_KEY_HERE"` with your actual API key. If you do not have an API key or prefer to enter it manually each time, you can leave the `.env` file without the `FMP_API_KEY` line, or leave the value empty (`FMP_API_KEY=""`).

## Configuration

The application attempts to load the API key from the `FMP_API_KEY` environment variable (which is typically loaded from the `.env` file).

*   If `FMP_API_KEY` is found in the environment, the API Key input field in the application window will be hidden.
*   If `FMP_API_KEY` is not found in the environment, the API Key input field will be visible, and you will need to enter your API key there.

## Usage

1.  **Run the application:**
    Navigate to the project directory in your terminal and run:
    ```bash
    python dcf.py
    ```

2.  **Enter parameters:**
    In the left panel, enter the required "Symbol" (e.g., AAPL) and any other desired parameters for the DCF analysis. If the API Key field is visible, enter your API key.

3.  **Submit the query:**
    Click the "Submit" button to fetch the data. The results will be displayed in the table on the right.

4.  **Interact with the table:**
    The table is powered by `tksheet` and provides Excel-like functionality, including:
    *   Single cell, column, and row selection.
    *   Column and row dragging and dropping.
    *   Column and row resizing.
    *   Copy, paste, cut, and delete operations.
    *   Inserting and deleting rows and columns (via right-click context menu).
    *   Showing and hiding rows and columns (via right-click context menu).

5.  **Use action buttons:**
    *   **Choose Columns:** Click to open a dialog to select which columns are displayed in the table.
    *   **Pivot Table:** Click to open a dialog to create a pivot table from the current data.
    *   **Export JSON:** Click to export the current table data to a JSON file in the `data/` directory. The filename will be timestamped and include the symbol and parameters used.

## Features

*   Fetch custom DCF data from Financial Modeling Prep API.
*   Interactive, Excel-like data table using `tksheet`.
*   Conditional display of API key input based on `.env` file.
*   Choose visible columns.
*   Create pivot tables.
*   Export data to JSON.
