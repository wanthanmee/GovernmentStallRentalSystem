import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, date
import sqlite3
import uuid
import calendar


'''
----------------------(Start Notes)--------------------------------------------
- Database name is "Government_Rental_System.db"
- Table name is "Payment"
- Table columns are: Payment_ID, Transaction_Date, Tenant_id, Rental_Amount,
                     Reference_No, Remark, and Upload_Slip
----------------------(End Notes)---------------------------------------------
'''

root = tk.Tk()
root.title("Admin Payment Management")
root.state("zoomed")

# Global connection object
conn = None


def setup_database():
	"""Setup the database with the new approval-related columns"""
	conn = sqlite3.connect("Government_Rental_System.db")
	cursor = conn.cursor()

	cursor.execute("""
        PRAGMA table_info(Payment)
    """)
	columns = [column[1] for column in cursor.fetchall()]

	if 'Gov_Slip' not in columns:
		cursor.execute("""
                ALTER TABLE Payment 
                ADD COLUMN Gov_Slip TEXT
            """)

	if 'Status' not in columns:
		cursor.execute("""
            ALTER TABLE Payment 
            ADD COLUMN Status TEXT DEFAULT 'Pending'
        """)

	if 'Approval_Date' not in columns:
		cursor.execute("""
            ALTER TABLE Payment 
            ADD COLUMN Approval_Date DATETIME
        """)

	conn.commit()
	conn.close()

#NOTE: Allow the admin to filter through the records via date and name
def update_days(*args):
	"""Update the days dropdown based on selected month and year"""
	month = int(start_month_var.get())
	year = int(start_year_var.get())
	days_in_month = calendar.monthrange(year, month)[1]

	# Update start date days
	start_day_dropdown['values'] = list(range(1, days_in_month + 1))
	if int(start_day_var.get()) > days_in_month:
		start_day_var.set(1)

	# Update end date days
	month = int(end_month_var.get())
	year = int(end_year_var.get())
	days_in_month = calendar.monthrange(year, month)[1]
	end_day_dropdown['values'] = list(range(1, days_in_month + 1))
	if int(end_day_var.get()) > days_in_month:
		end_day_var.set(1)


def apply_date_filter():
	"""Apply the date filter to the payment records"""
	try:
		# Create date objects for validation
		start_date = date(
			int(start_year_var.get()),
			int(start_month_var.get()),
			int(start_day_var.get())
		)
		end_date = date(
			int(end_year_var.get()),
			int(end_month_var.get()),
			int(end_day_var.get())
		)

		# Validate date range
		if start_date > end_date:
			messagebox.showerror("Error", "Start date must be before end date")
			return

		# Convert dates to string format for database query
		start_date_str = start_date.strftime('%Y-%m-%d')
		end_date_str = end_date.strftime('%Y-%m-%d')

		# Get records with date filter
		get_payment_record(start_date_str, end_date_str)

	except ValueError as e:
		messagebox.showerror("Error", f"Invalid date selection: {str(e)}")

def reset_filter():
	"""Reset the date filter and show all pending payments"""
	today = datetime.now()

	# Reset start date
	start_year_var.set(today.year)
	start_month_var.set(today.month)
	start_day_var.set(today.day)

	# Reset end date
	end_year_var.set(today.year)
	end_month_var.set(today.month)
	end_day_var.set(today.day)

	get_payment_record()
#-----------------------------------------------------------------------
#Function: get_payment_record
#Purpose: Retrieves the data record from the database
#-----------------------------------------------------------------------
def get_payment_record(start_date=None, end_date=None):
	"""
	Retrieves payment records from the database with optional date filtering.

	Args:
		start_date (str, optional): Start date in YYYY-MM-DD format
		end_date (str, optional): End date in YYYY-MM-DD format
	"""
	global conn

	if not conn:
		conn = sqlite3.connect("Government_Rental_System.db")

	cursor = conn.cursor()

	if start_date and end_date:
		# Convert input dates to datetime objects for comparison
		start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
		end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

		cursor.execute("""
            SELECT * FROM Payment 
            WHERE (Status = 'Pending' OR Status IS NULL)
            AND date(Transaction_Date) BETWEEN date(?) AND date(?)
            ORDER BY date(Transaction_Date) DESC
        """, (start_date, end_date))
	else:
		# Fetch all pending payments
		cursor.execute("""
            SELECT * FROM Payment 
            WHERE Status = 'Pending' OR Status IS NULL
            ORDER BY Transaction_Date DESC
        """)

	records = cursor.fetchall()

	# Clear and populate the listbox
	p_notif_listbox.delete(0, tk.END)

	# Store Payment_IDs in a dictionary using listbox index as key
	global payment_id_map
	payment_id_map = {}

	for idx, record in enumerate(records):
		payment_id = record[0]
		transaction_date_str = record[1]

		try:
			# Try to parse the date - handle both YYYY-MM-DD and MM/DD/YY formats
			try:
				# First try YYYY-MM-DD format
				transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d')
			except ValueError:
				# If that fails, try MM/DD/YY format
				transaction_date = datetime.strptime(transaction_date_str, '%m/%d/%y')

			# Display in MM/DD/YYYY format
			formatted_date = transaction_date.strftime('%m/%d/%Y')
		except ValueError:
			# If all parsing fails, use the original string
			formatted_date = transaction_date_str

		display_text = f"Payment ID: {payment_id} - Date: {formatted_date}"
		p_notif_listbox.insert(tk.END, display_text)
		payment_id_map[idx] = payment_id

	# Update the record count label
	record_count_label.config(text=f"Records found: {len(records)}")


def standardize_date_format():
	"""
	Ensures all dates in the Transaction_Date column are in YYYY-MM-DD format.
	Should be called once to standardize existing data.
	"""
	global conn

	if not conn:
		conn = sqlite3.connect("Government_Rental_System.db")

	cursor = conn.cursor()

	# Get all records
	cursor.execute("SELECT Payment_ID, Transaction_Date FROM Payment")
	records = cursor.fetchall()

	for payment_id, date_str in records:
		try:
			# Try to parse the date from MM/DD/YY format
			date_obj = datetime.strptime(date_str, '%m/%d/%y')
			# Convert to YYYY-MM-DD format
			standardized_date = date_obj.strftime('%Y-%m-%d')

			# Update the record
			cursor.execute("""
                UPDATE Payment 
                SET Transaction_Date = ? 
                WHERE Payment_ID = ?
            """, (standardized_date, payment_id))

		except ValueError:
			# Skip if the date is already in YYYY-MM-DD format or invalid
			continue

	conn.commit()

#-----------------------------------------------------------------------
#Function: show_full_payment_details
#Purpose: -notifies the admin of any payments made by the tenant
#          by displaying the Payment_ID and Transaction_Date in the
#          p_notif_listbox
#         -When the admin selects a record in the p_notif_listbox, the
#         full details of the record are displayed on the right frame
#         -Payment_ID, Transaction_Date, Tenant_id, Rental_Amount,
#          Reference_No,Remark, and Upload_Slip
#-----------------------------------------------------------------------
def show_full_payment_details(event):
    global conn, payment_id_map

    # Clear any existing widgets in the full_payment_details_frame
    for widget in full_payment_details_frame.winfo_children():
        widget.destroy()

    # Check if an item is selected in the listbox
    if not p_notif_listbox.curselection():
        return

    # Get the selected record index
    selected_index = p_notif_listbox.curselection()[0]
    payment_id = payment_id_map[selected_index]  # Get the actual Payment_ID

    # Fetch the selected record from the database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Payment WHERE Payment_ID = ?", (payment_id,))
    record = cursor.fetchone()

    if record:
        # Create labels to display the record details
        transaction_date_lbl = tk.Label(full_payment_details_frame, text="Transaction Date: ",
                                      font=("Helvetica", 14, "bold"), bg="#F5F5F5")
        transaction_date_lbl.grid(row=0, column=0, sticky='w', padx=10, pady=5)
        transaction_date_value = tk.Label(full_payment_details_frame, text=record[1],
                                        font=("Helvetica", 14), bg="#F5F5F5")
        transaction_date_value.grid(row=0, column=1, sticky='w', padx=10, pady=5)

        tenant_id_lbl = tk.Label(full_payment_details_frame, text="Tenant ID: ",
                                font=("Helvetica", 14, "bold"), bg="#F5F5F5")
        tenant_id_lbl.grid(row=1, column=0, sticky='w', padx=10, pady=5)
        tenant_id_value = tk.Label(full_payment_details_frame, text=str(record[2]),
                                 font=("Helvetica", 14), bg="#F5F5F5")
        tenant_id_value.grid(row=1, column=1, sticky='w', padx=10, pady=5)

        rental_amount_lbl = tk.Label(full_payment_details_frame, text="Amount Paid: ",
                                   font=("Helvetica", 14, "bold"), bg="#F5F5F5")
        rental_amount_lbl.grid(row=2, column=0, sticky='w', padx=10, pady=5)
        rental_amount_value = tk.Label(full_payment_details_frame,
                                     text="${:,.2f}".format(record[3]),
                                     font=("Helvetica", 14), bg="#F5F5F5")
        rental_amount_value.grid(row=2, column=1, sticky='w', padx=10, pady=5)

        ref_no_lbl = tk.Label(full_payment_details_frame, text="Reference No: ",
                             font=("Helvetica", 14, "bold"), bg="#F5F5F5")
        ref_no_lbl.grid(row=3, column=0, sticky='w', padx=10, pady=5)
        ref_no_value = tk.Label(full_payment_details_frame, text=str(record[4]),
                               font=("Helvetica", 14), bg="#F5F5F5")
        ref_no_value.grid(row=3, column=1, sticky='w', padx=10, pady=5)

        remark_lbl = tk.Label(full_payment_details_frame, text="Remarks: ",
                             font=("Helvetica", 14, "bold"), bg="#F5F5F5")
        remark_lbl.grid(row=4, column=0, sticky='w', padx=10, pady=5)
        remark_value = tk.Label(full_payment_details_frame, text=record[5],
                               font=("Helvetica", 14), bg="#F5F5F5")
        remark_value.grid(row=4, column=1, sticky='w', padx=10, pady=5)

        # Bank receipt button
        bank_receipt_btn = tk.Button(full_payment_details_frame, text="View Bank Receipt",
                                   font=("Helvetica", 12), bg="#ff8210", fg="white",
                                   command=lambda: view_bank_receipt(record[6]))
        bank_receipt_btn.grid(row=5, column=0, columnspan=2, pady=10)




#-----------------------------------------------------------------------
#Function: view_bank_receipt
#Purpose: - Retrieves the receipt sent by the tenant called "Upload_Slip"
#         - uses the file directory to display the document in the UI
#           (can be in any format)
#-----------------------------------------------------------------------
def view_bank_receipt():
    print("Viewing bank receipt...")
#-----------------------------------------------------------------------
#Function: approve_payment
#Purpose: - when the payment is approved, the GOVERNMENT RECEIPT is automatically
#           generated and it sends to the Tenant side.
#-----------------------------------------------------------------------
def approve_payment():
	global conn, payment_id_map

	# Ensure a payment is selected
	if not p_notif_listbox.curselection():
		messagebox.showwarning("Warning", "Please select a payment to approve.")
		return

	# Get the selected payment ID using the mapping
	selected_index = p_notif_listbox.curselection()[0]
	payment_id = payment_id_map[selected_index]

	# Update the payment status to "Approved" and set the Approval Date
	approval_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	cursor = conn.cursor()
	cursor.execute("""
        UPDATE Payment 
        SET Status = 'Approved', Approval_Date = ?
        WHERE Payment_ID = ?
    """, (approval_date, payment_id))

	conn.commit()

	# Show confirmation message
	messagebox.showinfo("Success", f"Payment ID {payment_id} approved successfully.")

	# Clear the full payment details frame
	for widget in full_payment_details_frame.winfo_children():
		widget.destroy()

	# Refresh the payment records list
	get_payment_record()


#-----------------------------------------------------------------------
#Function: view_transaction_history
#Purpose: - opens the transaction history window
#         - displays all the records of the approved payments
#-----------------------------------------------------------------------
def view_transaction_history():
    global conn

    # Create a new window
    history_window = tk.Toplevel()
    history_window.title("Transaction History")
    history_window.state("zoomed")

    # Create main container frame
    main_container = tk.Frame(history_window, bg="#F5F5F5")
    main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Create filter frame at the top
    filter_frame = tk.Frame(main_container, bg="#F5F5F5")
    filter_frame.pack(fill=tk.X, pady=(0, 10))

    # Date variables for history window
    years = list(range(2020, datetime.now().year + 2))
    months = list(range(1, 13))

    hist_start_year_var = tk.StringVar(value=datetime.now().year)
    hist_start_month_var = tk.StringVar(value=1)
    hist_start_day_var = tk.StringVar(value=1)

    hist_end_year_var = tk.StringVar(value=datetime.now().year)
    hist_end_month_var = tk.StringVar(value=datetime.now().month)
    hist_end_day_var = tk.StringVar(value=datetime.now().day)

    # Start date frame
    start_date_frame = tk.Frame(filter_frame, bg="#F5F5F5")
    start_date_frame.pack(side=tk.LEFT, padx=10)

    tk.Label(start_date_frame, text="Start Date:", font=("Helvetica", 12),
             bg="#F5F5F5").pack(side=tk.LEFT)

    hist_start_year_dropdown = ttk.Combobox(start_date_frame, textvariable=hist_start_year_var,
                                     values=years, width=6)
    hist_start_year_dropdown.pack(side=tk.LEFT, padx=2)

    hist_start_month_dropdown = ttk.Combobox(start_date_frame, textvariable=hist_start_month_var,
                                      values=months, width=4)
    hist_start_month_dropdown.pack(side=tk.LEFT, padx=2)

    hist_start_day_dropdown = ttk.Combobox(start_date_frame, textvariable=hist_start_day_var,
                                    width=4)
    hist_start_day_dropdown.pack(side=tk.LEFT, padx=2)

    # End date frame
    end_date_frame = tk.Frame(filter_frame, bg="#F5F5F5")
    end_date_frame.pack(side=tk.LEFT, padx=10)

    tk.Label(end_date_frame, text="End Date:", font=("Helvetica", 12),
             bg="#F5F5F5").pack(side=tk.LEFT)

    hist_end_year_dropdown = ttk.Combobox(end_date_frame, textvariable=hist_end_year_var,
                                   values=years, width=6)
    hist_end_year_dropdown.pack(side=tk.LEFT, padx=2)

    hist_end_month_dropdown = ttk.Combobox(end_date_frame, textvariable=hist_end_month_var,
                                    values=months, width=4)
    hist_end_month_dropdown.pack(side=tk.LEFT, padx=2)

    hist_end_day_dropdown = ttk.Combobox(end_date_frame, textvariable=hist_end_day_var,
                                  width=4)
    hist_end_day_dropdown.pack(side=tk.LEFT, padx=2)

    def update_history_days(*args):
        """Update the days dropdown based on selected month and year"""
        # Update start date days
        month = int(hist_start_month_var.get())
        year = int(hist_start_year_var.get())
        days_in_month = calendar.monthrange(year, month)[1]
        hist_start_day_dropdown['values'] = list(range(1, days_in_month + 1))
        if int(hist_start_day_var.get()) > days_in_month:
            hist_start_day_var.set(1)

        # Update end date days
        month = int(hist_end_month_var.get())
        year = int(hist_end_year_var.get())
        days_in_month = calendar.monthrange(year, month)[1]
        hist_end_day_dropdown['values'] = list(range(1, days_in_month + 1))
        if int(hist_end_day_var.get()) > days_in_month:
            hist_end_day_var.set(1)

    # Bind the update_days function
    for var in [hist_start_month_var, hist_start_year_var,
                hist_end_month_var, hist_end_year_var]:
        var.trace('w', update_history_days)

    # Initialize days in dropdowns
    update_history_days()

    def apply_history_filter():
        try:
            # Create date objects for validation
            start_date = date(
                int(hist_start_year_var.get()),
                int(hist_start_month_var.get()),
                int(hist_start_day_var.get())
            )
            end_date = date(
                int(hist_end_year_var.get()),
                int(hist_end_month_var.get()),
                int(hist_end_day_var.get())
            )

            # Validate date range
            if start_date > end_date:
                messagebox.showerror("Error", "Start date must be before end date")
                return

            # Clear existing items in treeview
            for item in tree.get_children():
                tree.delete(item)

            # Fetch filtered records
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Payment_ID, Transaction_Date, Tenant_id, Rental_Amount, 
                       Reference_No, Status, Approval_Date 
                FROM Payment 
                WHERE Status = 'Approved'
                AND date(Transaction_Date) BETWEEN date(?) AND date(?)
                ORDER BY Approval_Date DESC
            """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))

            # Insert filtered data into treeview
            for record in cursor.fetchall():
                formatted_amount = "${:,.2f}".format(record[3])
                display_record = (record[0], record[1], record[2], formatted_amount,
                                record[4], record[5], record[6])
                tree.insert('', tk.END, values=display_record)

            # Update record count
            record_count_var.set(f"Records found: {len(tree.get_children())}")

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date selection: {str(e)}")

    def reset_history_filter():
        # Reset date selections to defaults
        today = datetime.now()
        hist_start_year_var.set(today.year)
        hist_start_month_var.set(1)
        hist_start_day_var.set(1)
        hist_end_year_var.set(today.year)
        hist_end_month_var.set(today.month)
        hist_end_day_var.set(today.day)

        # Clear and reload all approved records
        for item in tree.get_children():
            tree.delete(item)

        cursor = conn.cursor()
        cursor.execute("""
            SELECT Payment_ID, Transaction_Date, Tenant_id, Rental_Amount, 
                   Reference_No, Status, Approval_Date 
            FROM Payment 
            WHERE Status = 'Approved'
            ORDER BY Approval_Date DESC
        """)

        for record in cursor.fetchall():
            formatted_amount = "${:,.2f}".format(record[3])
            display_record = (record[0], record[1], record[2], formatted_amount,
                            record[4], record[5], record[6])
            tree.insert('', tk.END, values=display_record)

        # Update record count
        record_count_var.set(f"Records found: {len(tree.get_children())}")

    # Filter buttons
    button_frame = tk.Frame(filter_frame, bg="#F5F5F5")
    button_frame.pack(side=tk.LEFT, padx=10)

    apply_filter_btn = tk.Button(button_frame, text="Apply Filter",
                               command=apply_history_filter, bg="#4CAF50", fg="white")
    apply_filter_btn.pack(side=tk.LEFT, padx=5)

    reset_filter_btn = tk.Button(button_frame, text="Reset",
                               command=reset_history_filter, bg="#f44336", fg="white")
    reset_filter_btn.pack(side=tk.LEFT, padx=5)

    # Record count label with StringVar
    record_count_var = tk.StringVar(value="Records found: 0")
    record_count_label = tk.Label(filter_frame, textvariable=record_count_var,
                                font=("Helvetica", 12), bg="#F5F5F5")
    record_count_label.pack(side=tk.RIGHT, padx=10)

    # Create Treeview frame
    tree_frame = tk.Frame(main_container, bg="#F5F5F5")
    tree_frame.pack(fill=tk.BOTH, expand=True)

    # Create Treeview with style
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"), foreground="#ff8210")
    style.configure("Treeview", font=("Helvetica", 13))

    # Create Treeview
    columns = ("Payment ID", "Transaction Date", "Tenant ID", "Amount", "Reference No",
               "Status", "Approval Date")
    tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

    # Set column headings
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)

    # Add scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    # Pack the Treeview and scrollbar
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create a frame for the view receipt button
    receipt_button_frame = tk.Frame(main_container, bg="#F5F5F5")
    receipt_button_frame.pack(fill=tk.X, pady=10)

    view_receipt_btn = tk.Button(receipt_button_frame, text="View Government Receipt",
                                font=("Helvetica", 12), bg="#ff8210", fg="white",
                                command=lambda: view_government_receipt(tree))
    view_receipt_btn.pack()

    # Load initial data
    reset_history_filter()
#-----------------------------------------------------------------------
#Function: view_government_receipt
#Purpose: - a user selects a record from the transaction history
#         - they press on the "View Receipt" button at the bottom to view the generated PDF
#-----------------------------------------------------------------------
def view_government_receipt():
    print("Viewing government receipt...")




#Main UI Setup
# Top frame
top_frame = tk.Frame(root, bg="#F5F5F5")
top_frame.pack(side=tk.TOP, fill=tk.X)

# Center label
for i in range(7):
    top_frame.grid_columnconfigure(i, weight=1)

tk.Label(top_frame, text="Admin - Payment Management",
         font=("helvetica", 30, "bold"), bg="#F5F5F5").grid(row=0, column=0,
         columnspan=7, padx=10, pady=20, sticky="nsew")

# Filter frame (new)
filter_frame = tk.Frame(root, bg="#F5F5F5")
filter_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

# Date variables
today = datetime.now()
years = list(range(2020, today.year + 2))
months = list(range(1, 13))

# Start date variables and dropdowns
start_year_var = tk.StringVar(value=today.year)
start_month_var = tk.StringVar(value=today.month)
start_day_var = tk.StringVar(value=today.day)

# End date variables and dropdowns
end_year_var = tk.StringVar(value=today.year)
end_month_var = tk.StringVar(value=today.month)
end_day_var = tk.StringVar(value=today.day)

# Start date frame
start_date_frame = tk.Frame(filter_frame, bg="#F5F5F5")
start_date_frame.pack(side=tk.LEFT, padx=10)

tk.Label(start_date_frame, text="Start Date:", font=("Helvetica", 12),
         bg="#F5F5F5").pack(side=tk.LEFT)

start_year_dropdown = ttk.Combobox(start_date_frame, textvariable=start_year_var,
                                 values=years, width=6)
start_year_dropdown.pack(side=tk.LEFT, padx=2)

start_month_dropdown = ttk.Combobox(start_date_frame, textvariable=start_month_var,
                                  values=months, width=4)
start_month_dropdown.pack(side=tk.LEFT, padx=2)

start_day_dropdown = ttk.Combobox(start_date_frame, textvariable=start_day_var,
                                width=4)
start_day_dropdown.pack(side=tk.LEFT, padx=2)

# End date frame
end_date_frame = tk.Frame(filter_frame, bg="#F5F5F5")
end_date_frame.pack(side=tk.LEFT, padx=10)

tk.Label(end_date_frame, text="End Date:", font=("Helvetica", 12),
         bg="#F5F5F5").pack(side=tk.LEFT)

end_year_dropdown = ttk.Combobox(end_date_frame, textvariable=end_year_var,
                               values=years, width=6)
end_year_dropdown.pack(side=tk.LEFT, padx=2)

end_month_dropdown = ttk.Combobox(end_date_frame, textvariable=end_month_var,
                                values=months, width=4)
end_month_dropdown.pack(side=tk.LEFT, padx=2)

end_day_dropdown = ttk.Combobox(end_date_frame, textvariable=end_day_var,
                              width=4)
end_day_dropdown.pack(side=tk.LEFT, padx=2)

# Bind the update_days function to the month and year changes
for var in [start_month_var, start_year_var, end_month_var, end_year_var]:
    var.trace('w', update_days)

# Initialize days in dropdowns
update_days()

# Filter buttons
button_frame = tk.Frame(filter_frame, bg="#F5F5F5")
button_frame.pack(side=tk.LEFT, padx=10)

apply_filter_btn = tk.Button(button_frame, text="Apply Filter",
                           command=apply_date_filter, bg="#4CAF50", fg="white")
apply_filter_btn.pack(side=tk.LEFT, padx=5)

reset_filter_btn = tk.Button(button_frame, text="Reset",
                           command=reset_filter, bg="#f44336", fg="white")
reset_filter_btn.pack(side=tk.LEFT, padx=5)

# Record count label
record_count_label = tk.Label(filter_frame, text="Records found: 0",
                            font=("Helvetica", 12), bg="#F5F5F5")
record_count_label.pack(side=tk.RIGHT, padx=10)

# Bottom frame
bottom_frame = tk.Frame(root, bg="#F5F5F5")
bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

# bottom frame
bottom_frame = tk.Frame(root, bg="#F5F5F5")
bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

# Configure grid layout for full y-axis fill
bottom_frame.grid_rowconfigure(0, weight=1)   # Make row stretch vertically
bottom_frame.grid_columnconfigure(0, weight=1)  # left frame
bottom_frame.grid_columnconfigure(1, weight=2)  # right frame

# left frame
left_frame = tk.Frame(bottom_frame, bg="blue")
left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

#Displays the transaction notifications
p_notif_listbox = tk.Listbox(left_frame, font=("helvetica", 12))
p_notif_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

p_notif_scrollbar = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=p_notif_listbox.yview)
p_notif_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Link Listbox to Scrollbar
p_notif_listbox.config(yscrollcommand=p_notif_scrollbar.set)

# Modify the existing listbox binding
p_notif_listbox.bind("<<ListboxSelect>>", show_full_payment_details)

# right frame
right_frame = tk.Frame(bottom_frame, bg="white")
right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

# Configure the grid in right_frame to allow centering and positioning of elements
# COLUMNS
right_frame.grid_columnconfigure(0, weight=1)  # Left spacer column
right_frame.grid_columnconfigure(1, weight=1)  # Center column
right_frame.grid_columnconfigure(2, weight=1)  # Right spacer column

# ROWS
right_frame.grid_rowconfigure(0, weight=0)  # Row for full_payment_details_frame
right_frame.grid_rowconfigure(1, weight=0)  # Row for approve button
right_frame.grid_rowconfigure(2, weight=1)  # Spacer row to push transaction button to the bottom

#Note: Will only appear when a record is chosen from the listbox
# Full Payment Details Frame (at the top)
full_payment_details_frame = tk.Frame(right_frame, bg="#F5F5F5", width=800, height=600)
full_payment_details_frame.grid(row=0, column=1, sticky="n", pady=15)

# Approve Button (just below full_payment_details_frame)
approve_btn = tk.Button(right_frame, text="Approve", font=("Helvetica", 16),
                        width=15, height=1, bg="#5e9918", fg="white", command=approve_payment)
approve_btn.grid(row=1, column=1, padx=10, pady=5)

# Transaction History Button (at the bottom)
transaction_history_btn = tk.Button(right_frame, text="View Transaction History", font=("Helvetica", 12),
                                    bg="#ff8210", fg="white",command=view_transaction_history)
transaction_history_btn.grid(row=2, column=1, sticky="n", padx=10, pady=5)

setup_database()
#testing purposes
standardize_date_format()  # Add this line
get_payment_record()

root.mainloop()
