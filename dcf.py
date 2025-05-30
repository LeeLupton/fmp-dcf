"""
A Tkinter application for fetching and displaying custom discounted cash flow data
from the Financial Modeling Prep API, with Excel-like table functionality using tksheet.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import json
import requests
import pandas as pd
import tksheet
from dotenv import load_dotenv

###############################################
#                CONFIG                       #
###############################################

# Load .env and get API key if present
load_dotenv()
API_KEY_DEFAULT = os.getenv("FMP_API_KEY", "")
ENDPOINT = "https://financialmodelingprep.com/stable/custom-discounted-cash-flow"


# Fields for the query form (API Key field will be conditionally included)
BASE_PARAM_FIELDS = [
    ("Symbol * (required)", "symbol", ""),  # Must fill or we error
    ("revenueGrowthPct", "revenueGrowthPct", ""),
    ("ebitdaPct", "ebitdaPct", ""),
    ("depreciationAndAmortizationPct", "depreciationAndAmortizationPct", ""),
    ("cashAndShortTermInvestmentsPct", "cashAndShortTermInvestmentsPct", ""),
    ("receivablesPct", "receivablesPct", ""),
    ("inventoriesPct", "inventoriesPct", ""),
    ("payablePct", "payablePct", ""),
    ("ebitPct", "ebitPct", ""),
    ("capitalExpenditurePct", "capitalExpenditurePct", ""),
    ("operatingCashFlowPct", "operatingCashFlowPct", ""),
    (
        "sellingGeneralAndAdministrativeExpensesPct",
        "sellingGeneralAndAdministrativeExpensesPct",
        ""
    ),
    ("taxRate", "taxRate", ""),
    ("longTermGrowthRate", "longTermGrowthRate", ""),
    ("costOfDebt", "costOfDebt", ""),
    ("costOfEquity", "costOfEquity", ""),
    ("marketRiskPremium", "marketRiskPremium", ""),
    ("beta", "beta", ""),
    ("riskFreeRate", "riskFreeRate", ""),
]

AGG_FUNCS = ["sum", "mean", "count", "min", "max"]

class CustomDCFUI(tk.Tk):
    """
    Main App Window:
      - Left panel: Param fields + "Submit" 
      - Right panel: tksheet table
      - Middle row of buttons: "Choose Columns" (hide/show), "Pivot Table", "Export JSON"
    """

    def __init__(self):
        super().__init__()
        self.title("Custom DCF with Excel-like Table (tksheet)")

        # ====== Frames for layout ====== 
        self.params_frame = tk.Frame(self)
        self.params_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nw")

        self.table_actions_frame = tk.Frame(self)
        self.table_actions_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nw")

        self.sheet_frame = tk.Frame(self)
        self.sheet_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ====== Build parameter fields ======
        self.entries = {}
        row_idx = 0

        # Only show API Key field if not present in .env
        self.api_key_in_env = bool(API_KEY_DEFAULT)
        param_fields = BASE_PARAM_FIELDS.copy()
        if not self.api_key_in_env:
            param_fields = [("API Key", "apikey", "")] + param_fields

        for label_text, param_name, default_val in param_fields:
            lbl = tk.Label(self.params_frame, text=label_text)
            lbl.grid(row=row_idx, column=0, sticky="w", pady=3)
            ent = tk.Entry(self.params_frame, width=30)
            # For API Key field, don't prefill if not in env
            if param_name == "apikey" and self.api_key_in_env:
                ent.insert(0, API_KEY_DEFAULT)
            elif default_val:
                ent.insert(0, default_val)
            ent.grid(row=row_idx, column=1, pady=3)
            self.entries[param_name] = ent
            row_idx += 1

        submit_btn = tk.Button(
            self.params_frame,
            text="Submit",
            command=self.submit_query
        )
        submit_btn.grid(row=row_idx, column=0, columnspan=2, pady=5, sticky="ew")

        # ====== Table action buttons ======
        col_btn = tk.Button(
            self.table_actions_frame,
            text="Choose Columns",
            command=self.open_column_chooser
        )
        col_btn.pack(side=tk.LEFT, padx=5)

        pivot_btn = tk.Button(
            self.table_actions_frame,
            text="Pivot Table",
            command=self.open_pivot_dialog
        )
        pivot_btn.pack(side=tk.LEFT, padx=5)

        export_btn = tk.Button(
            self.table_actions_frame,
            text="Export JSON",
            command=self.export_json
        )
        export_btn.pack(side=tk.LEFT, padx=5)

        # ====== The tksheet widget ======
        self.sheet = tksheet.Sheet(
            self.sheet_frame,
            width=800, height=500
        )
        self.sheet.enable_bindings((
            "single_select",
            "column_select",
            "row_select",
            "column_drag_and_drop",
            "row_drag_and_drop",
            "column_resize",
            "double_click_column_resize",
            "row_resize",
            "double_click_row_resize",
            "copy",
            "paste",
            "delete",
            "cut",
            "rc_insert_row",
            "rc_delete_row",
            "rc_insert_col",
            "rc_delete_col",
            "show_hide_rows",
            "show_hide_cols",
        ))
        self.sheet.pack(fill="both", expand=True)

        self.df = pd.DataFrame()
        self.last_params = {}

    def submit_query(self):
        '''Submit the query to the API and display results in the tksheet.
        Collect parameters from the entries, validate, and make the request.
        If successful, convert the response to a DataFrame and display it.
        '''
        params = {}
        # Use the same param_fields logic as in __init__
        param_fields = BASE_PARAM_FIELDS.copy()
        if not self.api_key_in_env:
            param_fields = [("API Key", "apikey", "")] + param_fields

        for (_, p_name, _) in param_fields:
            val = self.entries[p_name].get().strip()
            if val:
                params[p_name] = val

        # If API key is in .env, always use it (override any entry)
        if self.api_key_in_env:
            params["apikey"] = API_KEY_DEFAULT
        elif not params.get("apikey"):
            messagebox.showerror("Missing API Key", "API Key is required.")
            return

        if "symbol" not in params or not params["symbol"]:
            messagebox.showerror("Missing Symbol", "Symbol is required (e.g. AAPL).")
            return

        try:
            resp = requests.get(ENDPOINT, params=params, timeout=10)
        except Exception as e:
            messagebox.showerror("Request Error", str(e))
            return

        if resp.status_code != 200:
            messagebox.showerror(
                "HTTP Error",
                f"Status code: {resp.status_code}\nResponse: {resp.text}"
            )
            return

        try:
            data = resp.json()
        except Exception as e:
            messagebox.showerror(
                "JSON Parse Error",
                f"Couldn't parse response as JSON.\n{e}\nRaw: {resp.text}"
            )
            return

        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            data = [{"response": str(data)}]

        self.last_params = params
        self.df = pd.DataFrame(data) if data else pd.DataFrame()
        self.display_dataframe(self.df)

    def export_json(self):
        '''Export the current DataFrame to a JSON file with parameters in the filename.
        The filename will include the symbol and other parameters, formatted for safety.'''
        if self.df.empty:
            messagebox.showinfo("No Data", "No data to export. Please submit a query first.")
            return

        params = self.last_params
        symbol = params.get('symbol', 'data').upper()

        items = []
        for k in sorted(params):
            if k in ('symbol', 'apikey'):
                continue
            v = params[k]
            if v:
                safe_val = "".join(c for c in v if c.isalnum() or c in ['.', '-'])
                items.append(f"{k}-{safe_val}")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        name_parts = [symbol] + items + [timestamp]
        path = 'data/'
        name = "_".join(name_parts) + ".json"
        filename = path + name
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            with open(filename, 'w') as f:
                json_data = self.df.to_dict(orient='records')
                json.dump({'params': params, 'data': json_data}, f, indent=2)
            messagebox.showinfo("Export Successful", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def display_dataframe(self, df: pd.DataFrame):
        '''Display the given DataFrame in the tksheet widget.
        If the DataFrame is empty, clear the sheet.'''
        if df.empty:
            self.sheet.set_sheet_data([[]])
            return

        data_as_list = df.astype(str).values.tolist()
        headers = df.columns.tolist()

        self.sheet.set_sheet_data(data_as_list)
        self.sheet.headers(newheaders=headers)
        self.sheet.refresh()

    def open_column_chooser(self):
        '''Open a dialog to choose which columns to display in the tksheet.
        '''
        # If no data yet, show a message
        if self.df is None or self.df.empty:
            messagebox.showinfo("No Data", "No data available. Please submit a query first.")
            return

        dlg = ColumnChooserDialog(self, self.df.columns.tolist())
        self.wait_window(dlg)
        chosen = dlg.chosen_columns
        if chosen is None:
            return
        self.display_dataframe(self.df[chosen])

    def open_pivot_dialog(self):
        '''Open the pivot dialog to create a pivot table with filters.
        '''
        if self.df.empty:
            messagebox.showinfo("No Data", "No data available. Please submit a query first.")
            return
        dlg = PivotDialog(self, self.df)
        self.wait_window(dlg)
        if dlg.result_df is not None:
            self.display_dataframe(dlg.result_df)

class ColumnChooserDialog(tk.Toplevel):
    """
    Allows the user to pick which columns are visible (via checkboxes).
    """
    def __init__(self, parent, all_columns):
        super().__init__(parent)
        self.title("Choose Columns")
        self.chosen_columns = None
        self.var_map = {}

        for col in all_columns:
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(self, text=col, variable=var)
            cb.pack(anchor="w")
            self.var_map[col] = var

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", pady=5)
        ok_btn = tk.Button(btn_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def on_ok(self):
        """User clicked OK, collect selected columns."""
        selected = [c for c, v in self.var_map.items() if v.get()]
        self.chosen_columns = selected
        self.destroy()

    def on_cancel(self):
        """User cancelled, no columns chosen."""
        self.chosen_columns = None
        self.destroy()


class PivotDialog(tk.Toplevel):
    """
    Lets user create a pivot with:
       - index (row) column
       - columns field
       - values field
       - aggregation function
       - multiple "filters" (choose column => pick which values to keep)
    """
    def __init__(self, parent, df: pd.DataFrame):
        super().__init__(parent)
        self.title("Pivot Table + Filters")
        self.minsize(500, 400)  # ensure enough space to display filter rows
        self.df_original = df
        self.result_df = None

        # We'll copy the original DataFrame so we can safely manipulate/inspect unique values.
        self.df = df.copy()

        # Build combos for row/col/val/agg
        col_list = self.df.columns.tolist()

        # row/col/val combos
        row_label = tk.Label(self, text="Index (rows):")
        row_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.index_combo = ttk.Combobox(self, values=col_list, state="readonly")
        self.index_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        col_label = tk.Label(self, text="Columns:")
        col_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.columns_combo = ttk.Combobox(self, values=col_list, state="readonly")
        self.columns_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        val_label = tk.Label(self, text="Values:")
        val_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.values_combo = ttk.Combobox(self, values=col_list, state="readonly")
        self.values_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # agg func
        agg_label = tk.Label(self, text="Agg Func:")
        agg_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.agg_combo = ttk.Combobox(self, values=AGG_FUNCS, state="readonly")
        self.agg_combo.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        self.agg_combo.set(AGG_FUNCS[0])

        # filters
        filter_label = tk.Label(self, text="Filters:")
        filter_label.grid(row=4, column=0, sticky="ne", padx=5, pady=5)

        self.filters_frame = tk.Frame(self)
        self.filters_frame.grid(row=4, column=1, sticky="nsew", padx=5, pady=5)

        self.filter_rows = []
        add_filter_btn = tk.Button(
            self.filters_frame,
            text="Add Filter",
            command=self.add_filter_row
        )
        add_filter_btn.pack(side=tk.TOP, anchor="w", pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=5)
        gen_btn = tk.Button(btn_frame, text="Generate", command=self.on_generate)
        gen_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        if col_list:
            self.index_combo.set(col_list[0])
            if len(col_list) > 1:
                self.columns_combo.set(col_list[1])
            if len(col_list) > 2:
                self.values_combo.set(col_list[2])

    def add_filter_row(self):
        """Create a new filter row and display it immediately."""
        row = FilterRow(self.filters_frame, self.df)
        row.pack_filter()
        self.filter_rows.append(row)
        self.filters_frame.update_idletasks()

    def on_generate(self):
        """Apply filters, pivot the data, store in self.result_df, then close dialog."""
        df_filtered = self.df.copy()

        # Apply each filter row
        for filter_row in self.filter_rows:
            col = filter_row.column_combo.get()
            if not col:
                continue
            selected_vals = filter_row.selected_values
            if selected_vals is None:
                # If user never chose anything, skip
                continue
            # Keep only rows that match one of the selected values
            df_filtered = df_filtered[df_filtered[col].isin(selected_vals)]

        idx_col = self.index_combo.get()
        col_col = self.columns_combo.get()
        val_col = self.values_combo.get()
        agg = self.agg_combo.get()

        if not idx_col or not col_col or not val_col:
            messagebox.showerror("Pivot Error", "Please select row/columns/values fields.")
            return

        try:
            pivoted = pd.pivot_table(
                df_filtered,
                index=idx_col,
                columns=col_col,
                values=val_col,
                aggfunc=agg
            )
            pivoted = pivoted.reset_index()
            pivoted.columns.name = None
            pivoted = pivoted.rename_axis(None, axis=1)
            self.result_df = pivoted
        except Exception as e:
            messagebox.showerror("Pivot Error", str(e))
            return

        self.destroy()

class FilterRow:
    """
    A small "row" in the filters UI:
       - Combobox to pick which column to filter
       - "Select Values" button => opens a multi-select dialog
       - "Remove" button => (optionally) remove this row
    We store the user's chosen values in .selected_values
    """
    def __init__(self, parent, df: pd.DataFrame):
        self.parent = parent
        self.df = df
        self.frame = tk.Frame(parent)
        self.column_combo = ttk.Combobox(self.frame, values=df.columns.tolist(), width=20, state="readonly")
        self.select_btn = tk.Button(self.frame, text="Select Values", command=self.select_values)
        self.remove_btn = tk.Button(self.frame, text="Remove", command=self.remove_self)

        self.selected_values = None  # set after user picks from multi-list

    def pack_filter(self):
        """Pack this filter row into the parent frame."""
        self.frame.pack(fill=tk.X, pady=2, padx=5)
        self.column_combo.pack(side=tk.LEFT, padx=5)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        self.remove_btn.pack(side=tk.LEFT, padx=5)

    def remove_self(self):
        """Remove this filter row from the parent frame."""
        if messagebox.askyesno("Remove Filter", "Are you sure you want to remove this filter?"):
            # Remove from parent frame
            self.frame.pack_forget()
            # Destroy the frame to free resources
        self.frame.destroy()

    def select_values(self):
        """
        Show a dialog with unique values from the selected column.
        The user picks which ones to keep.
        """
        col = self.column_combo.get()
        if not col:
            messagebox.showerror("Filter Error", "Please pick a column first.")
            return

        uniques = self.df[col].dropna().unique()
        # Convert them all to string for display
        uniques_str = [str(x) for x in sorted(uniques)]

        # open a Toplevel with multi-select
        sel_dlg = MultiSelectDialog(self.frame, col, uniques_str)
        self.frame.wait_window(sel_dlg)
        if sel_dlg.selected_items is not None:
            # Convert strings back if desired, but here we can just store as str
            self.selected_values = sel_dlg.selected_items


class MultiSelectDialog(tk.Toplevel):
    """
    A simple multi-select listbox for picking from a list of items.
    """
    def __init__(self, parent, col_name, items):
        super().__init__(parent)
        self.title(f"Select values for {col_name}")
        self.selected_items = None
        self.items = items

        self.listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, height=15, width=50)
        self.listbox.pack(padx=5, pady=5, fill="both", expand=True)

        for it in items:
            self.listbox.insert(tk.END, it)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)
        ok_btn = tk.Button(btn_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def on_ok(self):
        '''User clicked OK, get selected items.'''
        sel_indices = self.listbox.curselection()
        if not sel_indices:
            self.selected_items = []
        else:
            self.selected_items = [self.items[i] for i in sel_indices]
        self.destroy()

    def on_cancel(self):
        '''User cancelled, no selection made.'''
        self.selected_items = None
        self.destroy()


def main():
    '''Main entry point to run the Custom DCF UI application.
    '''
    app = CustomDCFUI()
    app.mainloop()

if __name__ == "__main__":
    main()