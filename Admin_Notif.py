import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import sqlite3
import uuid
import os
import shutil

root = tk.Tk()
root.title("Admin Inbox")
root.state("zoomed")

# Variables
Unit = tk.StringVar()
Inbox = tk.StringVar(value="Inbox")
SearchText = tk.StringVar()
Subject = tk.StringVar()
AttachmentPath = tk.StringVar()
SendToAll = tk.BooleanVar()
PostCode = tk.StringVar()


# List of available units and inbox categories
inbox_set = ['Inbox', 'Read', 'Sent']

##FIXME: Placeholder for current user - replace with actual login system in production
current_user = "Admin"  # This line resolves the 'current_user' warnings


def create_database():
	conn = sqlite3.connect('db_messages6.db')
	c = conn.cursor()
	# Create notif_sent_reply table
	c.execute('''CREATE TABLE IF NOT EXISTS notif_sent_reply (
	                message_id TEXT PRIMARY KEY NOT NULL,
	                sender TEXT NOT NULL,
	                recipient TEXT NOT NULL,
	                subject TEXT NOT NULL,
	                message TEXT NOT NULL,
	                attachment TEXT,
	                timestamp_sent_reply DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
	            )''')

	# Create notif_inbox table with foreign key constraint on message_id
	c.execute('''CREATE TABLE IF NOT EXISTS notif_inbox (
	                message_id TEXT,
	                sender TEXT NOT NULL,
	                recipient TEXT NOT NULL,
	                subject TEXT NOT NULL,
	                message TEXT NOT NULL,
	                attachment TEXT,
	                timestamp_receive DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	                timestamp_read DATETIME,
	                status TEXT NOT NULL,
	                FOREIGN KEY (message_id) REFERENCES notif_sent_reply(message_id)
	            )''')

	# Create notif_deleted table with foreign key constraint on message_id
	c.execute('''CREATE TABLE IF NOT EXISTS notif_deleted (
	                message_id TEXT,
	                sender TEXT NOT NULL,
	                recipient TEXT NOT NULL,
	                subject TEXT NOT NULL,
	                message TEXT NOT NULL,
	                attachment TEXT,
	                source TEXT NOT NULL,
	                timestamp_deleted DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	                FOREIGN KEY (message_id) REFERENCES notif_sent_reply(message_id)
	            )''')
	conn.commit()
	conn.close()



# Call this function at the start of your program
create_database()
def generate_message_id():
	"""Generate a unique message ID"""
	return str(uuid.uuid4())

def filter_inbox(event):
	typed_text = Inbox.get().lower()
	filtered_inbox = [i for i in inbox_set if typed_text in i.lower()]
	inbox_combo['values'] = filtered_inbox

def search_stallID():
    postcode = SearchText.get().strip()  # Get search text from user input

    if not postcode:
        messagebox.showwarning("Input Required", "Please enter a postcode to search!")
        return

    conn = sqlite3.connect('govRental.db')
    c = conn.cursor()

    try:
        # Query to select stall_ids based on the provided postcode
        c.execute("SELECT stall_id FROM Stall WHERE Postcode = ?", (postcode,))
        stall_ids = [str(row[0]) for row in c.fetchall()]  # Fetch all stall_ids and convert to strings

        if stall_ids:
            result_label.config(text=f"Stall IDs: {', '.join(stall_ids)}")
        else:
            result_label.config(text="No stall IDs found for the entered postcode.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
    finally:
        conn.close()

# Create attachments directory if it doesn't exist
ATTACHMENTS_DIR = "attachments"
if not os.path.exists(ATTACHMENTS_DIR):
	os.makedirs(ATTACHMENTS_DIR)


def save_attachment(file_path):
	"""
	Save attachment to attachments directory and return the new path
	"""
	if not file_path:
		return None

	# Create unique filename
	file_ext = os.path.splitext(file_path)[1]
	new_filename = f"{str(uuid.uuid4())}{file_ext}"
	new_path = os.path.join(ATTACHMENTS_DIR, new_filename)

	# Copy file to attachments directory
	shutil.copy2(file_path, new_path)
	return new_path


def open_attachment(attachment_path):
	"""
	Open the attachment using system default application
	"""
	if attachment_path and os.path.exists(attachment_path):
		import platform
		if platform.system() == 'Darwin':  # macOS
			os.system(f'open "{attachment_path}"')
		elif platform.system() == 'Windows':  # Windows
			os.system(f'start "" "{attachment_path}"')
		else:  # Linux
			os.system(f'xdg-open "{attachment_path}"')
	else:
		messagebox.showerror("Error", "Attachment not found!")


def browse_file(window):
	file_types = (
		("All files", "*.*"),
		("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
		("Documents", "*.pdf *.doc *.docx *.txt")
	)
	file_path = filedialog.askopenfilename(
		title="Select file",
		parent=window,
		filetypes=file_types
	)
	if file_path:
		AttachmentPath.set(file_path)

def fetch_postcodes():
    conn = sqlite3.connect('govRental.db')
    c = conn.cursor()

    try:
        c.execute("SELECT DISTINCT Postcode FROM Stall")
        postcodes = [row[0] for row in c.fetchall()]
        return postcodes
    finally:
        conn.close()  # Ensure connection is closed after fetching


def fetch_stall_ids_by_postcode(postcode):
    conn = sqlite3.connect('govRental.db')
    c = conn.cursor()

    try:
        # Query to select stall_ids based on the provided postcode
        c.execute("SELECT stall_id FROM Stall WHERE Postcode = ?", (postcode,))
        stall_ids = [row[0] for row in c.fetchall()]  # Fetch all stall_ids
        return stall_ids
    finally:
        conn.close()  # Ensure connection is closed after fetching


def generate_message_id():
    return str(uuid.uuid4())  # Generates a unique ID using UUID

def insert_message_to_tables(sender, recipient, subject, message, attachment=None):
    """Insert message into both notif_sent_reply and notif_inbox tables"""
    conn = sqlite3.connect('db_messages6.db')
    c = conn.cursor()

    try:
        # Generate a unique message ID
        message_id = generate_message_id()

        # Insert into notif_sent_reply table
        c.execute(''' 
            INSERT INTO notif_sent_reply (
                message_id, sender, recipient, subject, message, attachment, timestamp_sent_reply
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (message_id, sender, recipient, subject, message, attachment))

        # Print the inserted message ID
        print(f"Inserted message into notif_sent_reply with ID: {message_id}")

        # Insert into notif_inbox table with 'New' status
        c.execute(''' 
            INSERT INTO notif_inbox (
                message_id, sender, recipient, subject, message, attachment, 
                timestamp_receive, timestamp_read, status
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, NULL, 'New')
        ''', (message_id, sender, recipient, subject, message, attachment))

        # Print the inserted message ID
        print(f"Inserted message into notif_inbox with ID: {message_id}")

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def send_message(send_to_all):
    subject = Subject.get()
    message = message_text.get(1.0, tk.END).strip()
    attachment_path = AttachmentPath.get()

    if not subject or not message:
        messagebox.showwarning("Missing Information", "Please enter both subject and message!")
        return

    conn_rental = sqlite3.connect('govRental.db')
    c_rental = conn_rental.cursor()

    try:
        if send_to_all:
            # Fetch all stall IDs across all postcodes
            c_rental.execute("SELECT Stall_ID FROM Stall")
            stall_IDs = [str(row[0]) for row in c_rental.fetchall()]
            print(f"All Stall IDs retrieved: {stall_IDs}")  # Debug print

            if not stall_IDs:
                messagebox.showwarning("No Stalls", "No stalls found in the database!")
                return

            # Insert message for each stall ID
            for stall_id in stall_IDs:
                if not insert_message_to_tables(current_user, stall_id, subject, message, attachment_path):
                    messagebox.showerror("Insert Error", "Failed to send message.")
                    return

        else:
            # Use specified postcode and selected stall ID
            postcode = PostCode.get().strip()
            if not postcode:
                messagebox.showwarning("Invalid Postcode", "Please enter a valid postcode!")
                return

            unit = stall_id_combo.get()
            if not unit:
                messagebox.showwarning("Missing Stall ID", "Please select a stall ID!")
                return

            # Insert message for the selected stall ID
            if not insert_message_to_tables(current_user, unit, subject, message, attachment_path):
                messagebox.showerror("Insert Error", "Failed to send message.")
                return

        messagebox.showinfo("Success", "Message sent successfully!")

    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
    finally:
        conn_rental.close()


def get_messages(user, category):
	conn = sqlite3.connect('db_messages6.db')
	c = conn.cursor()

	try:
		if category == "Sent":
			query = """
                SELECT message_id, sender, recipient, subject, message, attachment, timestamp_sent_reply, 'Sent' as status
                FROM notif_sent_reply 
                WHERE sender = ? 
                ORDER BY timestamp_sent_reply DESC
            """
			c.execute(query, (user,))

		elif category == "Read":
			query = """
                SELECT message_id, sender, recipient, subject, message, attachment, timestamp_receive, status
                FROM notif_inbox 
                WHERE recipient = ? 
                AND status = 'Read'
                ORDER BY timestamp_receive DESC
            """
			c.execute(query, (user,))

		else:  # "Inbox" - new messages
			query = """
                SELECT message_id, sender, recipient, subject, message, attachment, timestamp_receive, status
                FROM notif_inbox 
                WHERE recipient = ? 
                AND status = 'New'
                ORDER BY timestamp_receive DESC
            """
			c.execute(query, (user,))

		return c.fetchall()

	except sqlite3.Error as e:
		print(f"Database error: {e}")
		return []
	finally:
		conn.close()


def update_message_display():
	""" Update the message listbox with messages from the selected category """
	message_listbox.delete(0, tk.END)
	selected_category = Inbox.get()
	messages = get_messages(current_user, selected_category)

	for message in messages:
		message_id, sender, recipient, subject, message_text, attachment, timestamp, status = message

		# Format timestamp for display
		try:
			timestamp_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
			formatted_date = timestamp_obj.strftime("%Y-%m-%d %H:%M")
		except (ValueError, TypeError):
			formatted_date = "Unknown date"

		# Create display text based on category
		if selected_category == "Sent":
			if recipient == "All Units":
				display_text = f"To: All Units | Subject: {subject} | Date: {formatted_date}"
			else:
				display_text = f"To: {recipient} | Subject: {subject} | Date: {formatted_date}"
		else:
			display_text = f"From: {sender} | Subject: {subject} | Date: {formatted_date}"

		# Add attachment indicator if present
		if attachment:
			display_text += " 📎"

		message_listbox.insert(tk.END, display_text)

		# Set background color for new messages
		if status == 'New':
			message_listbox.itemconfig(message_listbox.size() - 1, {'bg': '#FFE4B5'})  # Light orange background


def show_full_message(event):
    selection = message_listbox.curselection()
    if not selection:
        return

    selected_index = selection[0]
    selected_category = Inbox.get()
    messages = get_messages(current_user, selected_category)
    selected_message = messages[selected_index]

    # Unpack the message details
    message_id, sender, recipient, subject, message, attachment, timestamp, status = selected_message

    # Clear previous content
    for widget in full_message_frame.winfo_children():
        widget.destroy()

    # Create a new frame for message details
    details_frame = tk.Frame(full_message_frame, bg="#F5F5F5")
    details_frame.pack(fill=tk.X, padx=10, pady=10)

    # Add message details
    tk.Label(details_frame, text=f"Subject: {subject}", font=("Helvetica", 12, "bold"), bg="#F5F5F5", anchor="w").pack(fill=tk.X)
    tk.Label(details_frame, text=f"From: {sender}", font=("Helvetica", 12), bg="#F5F5F5", anchor="w").pack(fill=tk.X)
    tk.Label(details_frame, text=f"To: {recipient}", font=("Helvetica", 12), bg="#F5F5F5", anchor="w").pack(fill=tk.X)
    tk.Label(details_frame, text=f"Date: {timestamp}", font=("Helvetica", 10), bg="#F5F5F5", anchor="w").pack(fill=tk.X)

    if attachment:
	    attachment_frame = tk.Frame(details_frame, bg="#F5F5F5")
	    attachment_frame.pack(fill=tk.X, pady=5)

	    attachment_label = tk.Label(
		    attachment_frame,
		    text=f"📎 {os.path.basename(attachment)}",
		    font=("Helvetica", 10),
		    bg="#F5F5F5",
		    fg="blue",
		    cursor="hand2"
	    )
	    attachment_label.pack(side=tk.LEFT)
	    attachment_label.bind("<Button-1>", lambda e: open_attachment(attachment))

    # Create a frame for the message body and replies
    message_body_frame = tk.Frame(full_message_frame)
    message_body_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # Add scrollbar
    scrollbar = tk.Scrollbar(message_body_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Add canvas for scrolling
    canvas = tk.Canvas(message_body_frame, yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=canvas.yview)

    # Create a frame inside the canvas for message content
    content_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=content_frame, anchor="nw")

    # Split the message into original message and replies
    message_parts = message.split("\n--- Reply from ")
    original_message = message_parts[0]

    # Display original message
    original_message_frame = tk.Frame(content_frame, bg="#ffcf90", bd=1, relief=tk.SOLID)
    original_message_frame.pack(fill=tk.X, padx=5, pady=5)

    tk.Label(original_message_frame, text="Original Message", font=("Helvetica", 10, "bold"), bg="#ffcf90").pack(anchor="w")
    tk.Label(original_message_frame, text=original_message, font=("Helvetica", 10), bg="#ffcf90", justify=tk.LEFT, wraplength=700).pack(anchor="w", padx=5, pady=5)

    # Display replies
    if len(message_parts) > 1:
        tk.Label(content_frame, text="Replies:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(10, 5))
        for reply in message_parts[1:]:
            reply_frame = tk.Frame(content_frame, bg="white", bd=1, relief=tk.SOLID)
            reply_frame.pack(fill=tk.X, padx=5, pady=5)

            # Split the reply into sender and content
            try:
                reply_sender, reply_content = reply.split(" ---\n", 1)
            except ValueError:
                # Handle cases where the format might be different
                reply_sender = "Unknown"
                reply_content = reply

            tk.Label(reply_frame, text=f"Reply from {reply_sender}", font=("Helvetica", 10, "bold"), bg="white").pack(anchor="w")
            tk.Label(reply_frame, text=reply_content, font=("Helvetica", 10), bg="white", justify=tk.LEFT, wraplength=700).pack(anchor="w", padx=5, pady=5)

    # Update scroll region
    content_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # Add reply frame at the bottom
    reply_frame = tk.Frame(full_message_frame, bg="#F5F5F5")
    reply_frame.pack(fill=tk.X, padx=10, pady=10)

    # Add reply text field
    reply_text = tk.Text(reply_frame, height=4, font=("Helvetica", 12))
    reply_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

    # Add reply button
    reply_button = tk.Button(
        reply_frame,
        text="Send Reply",
        font=("Helvetica", 12),
        bg="#ff8210",
        fg="white",
        command=lambda: handle_reply_send(
            sender=current_user,
            recipient=sender,  # Send reply to original sender
            subject=f"Re: {subject.replace('Re: ', '')}", # Avoid multiple "Re:" prefixes
            reply_message=reply_text.get("1.0", tk.END).strip(),
            original_message_id=message_id,
            reply_text=reply_text
        )
    )
    reply_button.pack(side=tk.RIGHT)

    if status == "New":
        mark_message_as_read(message_id)

def mark_message_as_read(message_id):
	"""
	Mark a message as read in the notif_inbox table
	"""
	conn = sqlite3.connect('db_messages6.db')
	c = conn.cursor()

	try:
		# First check if the message is in 'New' status
		c.execute("""
            SELECT status 
            FROM notif_inbox 
            WHERE message_id = ? AND recipient = ? AND status = 'New'
        """, (message_id, current_user))

		if c.fetchone():  # Only update if message is in 'New' status
			current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			c.execute("""
                UPDATE notif_inbox 
                SET status = 'Read', timestamp_read = ? 
                WHERE message_id = ? AND recipient = ? AND status = 'New'
            """, (current_timestamp, message_id, current_user))
			conn.commit()
	except sqlite3.Error as e:
		print(f"Database error: {e}")
		conn.rollback()
	finally:
		conn.close()
		update_message_display()


def delete_message():
	"""
	Delete selected message from inbox/sent_reply and move it to delete table
	Only deletes from the user's perspective (admin in this case)
	"""
	selected_index = message_listbox.curselection()
	if not selected_index:
		messagebox.showwarning("Selection Error", "Please select a message to delete.")
		return

	selected_category = Inbox.get()
	messages = get_messages(current_user, selected_category)

	if selected_index[0] >= len(messages):
		messagebox.showwarning("Error", "Invalid selection.")
		return

	message = messages[selected_index[0]]
	message_id = message[0]  # First element is message_id

	# Confirm deletion
	if not messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this message?"):
		return

	conn = sqlite3.connect('db_messages6.db')
	c = conn.cursor()

	try:
		# Begin transaction
		conn.execute('BEGIN')

		# Store message in notif_deleted table
		c.execute("""
            INSERT INTO notif_deleted (
                message_id, sender, recipient, subject, message, 
                attachment, source, timestamp_deleted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
			message_id,
			message[1],  # sender
			message[2],  # recipient
			message[3],  # subject
			message[4],  # message
			message[5],  # attachment
			selected_category  # source table
		))

		# Remove from appropriate source table based on category
		if selected_category == "Sent":
			# Delete from notif_sent_reply where current user is sender
			c.execute("""
                DELETE FROM notif_sent_reply 
                WHERE message_id = ? AND sender = ?
            """, (message_id, current_user))
		else:
			# Delete from notif_inbox where current user is recipient
			c.execute("""
                DELETE FROM notif_inbox 
                WHERE message_id = ? AND recipient = ?
            """, (message_id, current_user))

		conn.commit()
		messagebox.showinfo("Success", "Message deleted successfully")

		# Refresh the message display
		update_message_display()

		# Clear the full message display
		for widget in full_message_frame.winfo_children():
			widget.destroy()

	except sqlite3.Error as e:
		conn.rollback()
		messagebox.showerror("Error", f"Failed to delete message: {str(e)}")
	finally:
		conn.close()

def compose_message():
    global compose_win, message_text, PostCode, stall_id_combo, note_label, Subject, AttachmentPath

    compose_win = tk.Toplevel(root)
    compose_win.title("Compose Message")
    compose_win.geometry("800x600")
    compose_win.config(bg="#D3D3D3")

    main_frame = tk.Frame(compose_win, bg="#D3D3D3")
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    main_frame.grid_columnconfigure(1, weight=1)

    # Send to All Checkbox
    SendToAll = tk.BooleanVar(value=False)
    send_all_cb = tk.Checkbutton(
        main_frame,
        text="Send to ALL Units (across all postcodes)",
        variable=SendToAll,
        font=("helvetica", 12),
        bg="#D3D3D3",
        command=lambda: toggle_postcode_unit_fields(SendToAll.get(), postcode_combo, stall_id_combo, note_label)
    )
    send_all_cb.grid(row=0, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

    # Postcode Entry
    PostCode = tk.StringVar()
    tk.Label(main_frame, text="Search by Postcode", font=("helvetica", 16), bg="#D3D3D3").grid(
        row=1, column=0, padx=10, pady=10, sticky="w")
    postcode_combo = ttk.Combobox(main_frame, textvariable=PostCode, font=("helvetica", 16), width=40)
    postcode_combo['values'] = fetch_postcodes()  # Assumes this function returns a list of postcodes
    postcode_combo.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

    # Trigger filtering function when a postcode is selected
    postcode_combo.bind("<<ComboboxSelected>>", lambda e: update_stall_ids(PostCode.get()))

    # Stall ID Combo Box
    tk.Label(main_frame, text="Stall ID", font=("helvetica", 16), bg="#D3D3D3").grid(
        row=2, column=0, padx=10, pady=10, sticky="w")
    stall_id_combo = ttk.Combobox(main_frame, font=("helvetica", 16), width=40)
    stall_id_combo.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

    # Note label for auto-selection
    note_label = tk.Label(
        main_frame,
        text="Note: If no unit is selected, message will be sent to all units in the postcode",
        font=("helvetica", 12, "italic"),
        fg="gray",
        bg="#D3D3D3"
    )
    note_label.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

    # Subject Entry
    Subject = tk.StringVar()
    tk.Label(main_frame, text="Subject", font=("helvetica", 16), bg="#D3D3D3").grid(
        row=4, column=0, padx=10, pady=10, sticky="w")
    tk.Entry(main_frame, textvariable=Subject, font=("helvetica", 16)).grid(
        row=4, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

    # Message Text Area
    tk.Label(main_frame, text="Message", font=("helvetica", 16), bg="#D3D3D3").grid(
        row=5, column=0, padx=10, pady=10, sticky="nw")
    message_text = tk.Text(main_frame, font=("helvetica", 16), width=50, height=10)
    message_text.grid(row=5, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

    main_frame.grid_rowconfigure(5, weight=1)

    # Attachment Section
    AttachmentPath = tk.StringVar()
    tk.Label(main_frame, text="Attachment", font=("helvetica", 16), bg="#D3D3D3").grid(
        row=6, column=0, padx=10, pady=10, sticky="w")
    tk.Entry(main_frame, textvariable=AttachmentPath, font=("helvetica", 16), state='readonly').grid(
        row=6, column=1, padx=10, pady=10, sticky="ew")
    tk.Button(main_frame, text="Browse", font=("helvetica", 16),
              command=lambda: browse_file(compose_win)).grid(
        row=6, column=2, padx=10, pady=10, sticky="e")

    # Send Button
    send_button = tk.Button(main_frame, text="Send", font=("helvetica", 16),
                            bg="#ff8210", fg="white",
                            command=lambda: send_message(SendToAll.get()))
    send_button.grid(row=7, column=1, padx=10, pady=20, sticky="ew")

def update_stall_ids(selected_postcode):
    # Fetch stall IDs for the selected postcode and update stall_id_combo values
    stall_ids = fetch_stall_ids_by_postcode(selected_postcode)  # Assumes this function returns a list of stall IDs
    stall_id_combo['values'] = stall_ids  # Update ComboBox options

def toggle_postcode_unit_fields(send_to_all, postcode_entry, unit_combo, note_label):
    """Toggle the state of postcode and unit fields based on Send to All checkbox"""
    if send_to_all:
        postcode_entry.configure(state='disabled')
        unit_combo.configure(state='disabled')
        note_label.configure(text="Note: Message will be sent to ALL units across ALL postcodes")
    else:
        postcode_entry.configure(state='normal')
        unit_combo.configure(state='normal')
        note_label.configure(text="Note: If no unit is selected, message will be sent to all units in the postcode")


def reply_message(original_sender, original_subject, original_message):
	reply_win = tk.Toplevel(root)
	reply_win.title("Reply Message")
	reply_win.geometry("800x600")
	reply_win.config(bg="#D3D3D3")

	# Create main frame
	main_frame = tk.Frame(reply_win, bg="#D3D3D3")
	main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

	# Recipient and Subject display
	tk.Label(main_frame, text=f"To: {original_sender}", font=("Helvetica", 14), bg="#D3D3D3").pack(anchor="w")
	tk.Label(main_frame, text=f"Subject: Re: {original_subject}", font=("Helvetica", 14, "bold"), bg="#D3D3D3").pack(
		anchor="w")

	# Frame for previous messages
	previous_messages_frame = tk.Frame(main_frame)
	previous_messages_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

	# Scrollable text area for previous messages
	previous_messages = tk.Text(previous_messages_frame, font=("Helvetica", 12), wrap=tk.WORD, padx=10, pady=10)
	previous_messages.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
	previous_messages.insert(tk.END, f"From: {original_sender}\nSubject: {original_subject}\n\n{original_message}\n\n")
	previous_messages.config(state=tk.DISABLED)  # Disable editing

	# Scrollbar for previous messages
	scrollbar = tk.Scrollbar(previous_messages_frame, command=previous_messages.yview)
	scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
	previous_messages.config(yscrollcommand=scrollbar.set)

	# Frame for new message
	new_message_frame = tk.Frame(main_frame)
	new_message_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

	tk.Label(new_message_frame, text="Your Reply:", font=("Helvetica", 14), bg="#D3D3D3").pack(anchor="w")

	# Text area for user reply
	reply_text = tk.Text(new_message_frame, font=("Helvetica", 12), wrap=tk.WORD, height=5)
	reply_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

	# Send button for sending the reply
	send_reply_button = tk.Button(main_frame, text="Send Reply", font=("Helvetica", 12), bg="#ff8210", fg="white",
	                              command=lambda: send_reply(original_sender, f"Re: {original_subject}",
	                                                         reply_text.get(1.0, tk.END).strip(), reply_win))
	send_reply_button.pack(pady=10)


def send_reply(sender, recipient, subject, reply_message, original_message_id):
	"""
	Send a reply message and store it in both notif_sent_reply and notif_inbox tables
	"""
	if not reply_message.strip():
		messagebox.showwarning("Missing Reply", "Please enter your reply message!")
		return False

	conn = sqlite3.connect('db_messages6.db')
	c = conn.cursor()

	try:
		# Generate a new message_id for the reply
		new_message_id = generate_message_id()
		current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		# First, get the original message thread
		c.execute("""
            SELECT message FROM notif_sent_reply 
            WHERE message_id = ?
        """, (original_message_id,))
		original_message = c.fetchone()[0]

		# Create the updated message thread content
		updated_message = f"{original_message}\n--- Reply from {sender} ---\n{current_timestamp}: {reply_message}"

		# Insert reply into notif_sent_reply
		c.execute("""
            INSERT INTO notif_sent_reply (
                message_id, sender, recipient, subject, message, 
                attachment, timestamp_sent_reply
            ) VALUES (?, ?, ?, ?, ?, NULL, ?)
        """, (new_message_id, sender, recipient, subject, updated_message, current_timestamp))

		# Insert reply into notif_inbox
		c.execute("""
            INSERT INTO notif_inbox (
                message_id, sender, recipient, subject, message,
                attachment, timestamp_receive, timestamp_read, status
            ) VALUES (?, ?, ?, ?, ?, NULL, ?, NULL, 'New')
        """, (new_message_id, sender, recipient, subject, updated_message, current_timestamp))

		conn.commit()
		messagebox.showinfo("Reply Sent", "Your reply has been sent successfully!")
		return True

	except sqlite3.Error as e:
		print(f"Database error: {e}")
		conn.rollback()
		messagebox.showerror("Error", "Failed to send reply. Please try again.")
		return False
	finally:
		conn.close()

def handle_reply_send(sender, recipient, subject, reply_message, original_message_id, reply_text):
    """Helper function to handle reply sending and UI updates"""
    if send_reply(sender, recipient, subject, reply_message, original_message_id):
        reply_text.delete("1.0", tk.END)  # Clear reply field
        update_message_display()  # Refresh message list
        show_full_message(None)  # Refresh full message view


# Main UI setup
entries_frame = tk.Frame(root, bg="#F5F5F5")
entries_frame.pack(side=tk.TOP, fill=tk.X)

for i in range(7):
	entries_frame.grid_columnconfigure(i, weight=1)

tk.Label(entries_frame, text="Admin - INBOX", font=("helvetica", 30, "bold"), bg="#F5F5F5").grid(row=0, column=0,
                                                                                                 columnspan=7,
                                                                                                 padx=10, pady=20,
                                                                                                 sticky="nsew")

tk.Label(entries_frame, text="Unit:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=0, padx=10, pady=10,
                                                                                 sticky="nsew")
StallID_combo = tk.Entry(entries_frame, textvariable=Unit, font=("helvetica", 16), width=30)
StallID_combo.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

tk.Label(entries_frame, text="Category:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=2, padx=10, pady=10,
                                                                                     sticky="nsew")
inbox_combo = ttk.Combobox(entries_frame, textvariable=Inbox, font=("helvetica", 16), width=30, values=inbox_set)
inbox_combo.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")
inbox_combo.bind("<KeyRelease>", filter_inbox)
inbox_combo.bind("<<ComboboxSelected>>", lambda e: update_message_display())

tk.Label(entries_frame, text="Enter Postcode:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=4, padx=10,
                                                                                        pady=10, sticky="nsew")
tk.Entry(entries_frame, textvariable=SearchText, font=("helvetica", 16), width=30).grid(row=1, column=5, padx=10,
                                                                                        pady=10, sticky="nsew")
tk.Button(entries_frame, text="Search", font=("helvetica", 16), fg="white", bg="#ff8210", command=search_stallID).grid(
	row=1, column=6, padx=10, pady=10, sticky="nsew")

# Create a frame for the buttons
button_frame = tk.Frame(entries_frame, bg="#F5F5F5")
button_frame.grid(row=4, column=2, columnspan=3, padx=10, pady=10, sticky="ew")

# Configure the button frame columns
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)
button_frame.columnconfigure(2, weight=1)

# Add the buttons to the button frame
tk.Button(button_frame, text="Compose Message", font=("helvetica", 16), bg="#ff8210", fg="white",
          command=compose_message).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
tk.Button(button_frame, text="Delete Message", font=("helvetica", 16), bg="#ff8210", fg="white",
          command=delete_message).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

# Adjust the results label row if needed
result_label = tk.Label(entries_frame, text="Results: ", font=("helvetica", 16), bg="#F5F5F5")
result_label.grid(row=5, column=0, columnspan=7, padx=10, pady=10, sticky="w")

# Message display setup
lower_frame = tk.Frame(root)
lower_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

message_frame = tk.Frame(lower_frame)
message_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

message_listbox = tk.Listbox(message_frame, font=("helvetica", 12))
message_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

message_scrollbar = tk.Scrollbar(message_frame, orient=tk.VERTICAL, command=message_listbox.yview)
message_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
message_listbox.config(yscrollcommand=message_scrollbar.set)

message_listbox.bind("<<ListboxSelect>>", show_full_message)

# RIGHT FRAME

full_message_frame = tk.Frame(lower_frame)
full_message_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

full_message_text = tk.Text(full_message_frame, font=("helvetica", 12), wrap=tk.WORD)
full_message_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Initialize the message display
update_message_display()

root.mainloop()