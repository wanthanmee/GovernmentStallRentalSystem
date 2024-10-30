import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import sqlite3
import uuid
import os
import shutil

root = tk.Tk()
root.title("Tenant Inbox")
root.state("zoomed")

Unit = tk.StringVar()
Inbox = tk.StringVar(value="Inbox")
SearchText = tk.StringVar()
Subject = tk.StringVar()
AttachmentPath = tk.StringVar()
SendToAll = tk.BooleanVar()
PostCode = tk.StringVar()

# List of available units and inbox categories
unit_set = ['Unit 101', 'Unit 202', 'Unit 303', 'Unit 304', 'Unit 305', 'Unit 306', 'Unit 401', 'Unit 402']
inbox_set = ['Inbox', 'Read', 'Sent']

# Mock database for stalls (replace with actual database later)
stall_database = {
    "12345": ["Unit 101", "Unit 202", "Unit 303"],
    "67890": ["Unit 304", "Unit 305", "Unit 306"],
    "11111": ["Unit 401", "Unit 402"]
}

##FIXME: Placeholder for current user - replace with actual login system in production
#current_user = "TenantName"  # This line resolves the 'current_user' warnings

## FIXME: Testing purposes, hard-coded strings
# These are global variables
g_recipient = "Unit 101"
g_status = "Inbox"

def generate_message_id():
	"""Generate a unique message ID"""
	return str(uuid.uuid4())

def filter_units(event):
	typed_text = Unit.get().lower()
	filtered_units = [u for u in unit_set if typed_text in u.lower()]
	unit_combo['values'] = filtered_units


def filter_inbox(event):
	typed_text = Inbox.get().lower()
	filtered_inbox = [i for i in inbox_set if typed_text in i.lower()]
	inbox_combo['values'] = filtered_inbox

def filter_units_by_postcode(*args):
	"""
	Filter units based on entered Postcode
	"""
	postcode = PostCode.get().strip()
	if postcode in stall_database:
		unit_combo['values'] = stall_database[postcode]
	else:
		unit_combo['values'] = []
	Unit.set('')  # Clear current selection


def search_units():
	search_text = SearchText.get().lower()
	filtered_units = [u for u in unit_set if search_text in u.lower()]
	result_label.config(text="Results: " + ", ".join(filtered_units))


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

def insert_message_to_tables(sender, recipient, subject, message, attachment=None):
	"""Insert message into both notif_sent_reply and notif_inbox tables"""
	conn = sqlite3.connect('db_messages6.db')
	c = conn.cursor()

	try:
		# Generate a unique message ID
		message_id = generate_message_id()
		current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		# Insert into notif_sent_reply table
		c.execute('''
            INSERT INTO notif_sent_reply (
                message_id, sender, recipient, subject, message, attachment, timestamp_sent_reply
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (message_id, sender, recipient, subject, message, attachment, current_timestamp))

		# Insert into notif_inbox table with 'New' status
		c.execute('''
            INSERT INTO notif_inbox (
                message_id, sender, recipient, subject, message, attachment, 
                timestamp_receive, timestamp_read, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 'New')
        ''', (message_id, sender, recipient, subject, message, attachment, current_timestamp))

		conn.commit()
		return True
	except sqlite3.Error as e:
		print(f"Database error: {e}")
		conn.rollback()
		return False
	finally:
		conn.close()


def send_message():
	current_user= g_recipient
	subject = Subject.get()
	message = message_text.get(1.0, tk.END).strip()
	attachment_path = AttachmentPath.get()

	if not subject or not message:
		messagebox.showwarning("Missing Information", "Please enter both subject and message!")
		return

	if SendToAll.get():
		postcode = PostCode.get().strip()
		if postcode not in stall_database:
			messagebox.showwarning("Invalid postcode", "Please enter a valid postcode!")
			return
		units = stall_database[postcode]
	else:
		if not Unit.get():
			messagebox.showwarning("Missing Unit", "Please select a unit!")
			return
		units = [Unit.get()]

	# Save attachment if present
	stored_attachment_path = None
	if attachment_path:
		stored_attachment_path = save_attachment(attachment_path)

	success = False

	if SendToAll.get():
		# Send to all units in the postcode
		for recipient in units:
			success = insert_message_to_tables(
				current_user,
				recipient,
				subject,
				message,
				stored_attachment_path
			)
			if not success:
				break
	else:
		# Send to single unit
		success = insert_message_to_tables(
			current_user,
			units[0],
			subject,
			message,
			stored_attachment_path
		)

	if success:
		update_message_display()
		messagebox.showinfo("Success", "Message sent successfully!")
		compose_win.destroy()
	else:
		messagebox.showerror("Error", "Failed to send message")

def get_messages(user, category):
	"""
	Fetch messages based on user and category from appropriate tables
	"""
	conn = sqlite3.connect('db_messages6.db')
	c = conn.cursor()

	try:
		if category == "Sent":
			# Fetch sent messages from notif_sent_reply
			query = """
                SELECT 
                    message_id,
                    sender,
                    recipient,
                    subject,
                    message,
                    attachment,
                    timestamp_sent_reply,
                    'Sent' as status
                FROM notif_sent_reply 
                WHERE sender = ? 
                ORDER BY timestamp_sent_reply DESC
            """
			c.execute(query, (user,))

		elif category == "Read":
			# Fetch read messages from notif_inbox
			query = """
                SELECT 
                    message_id,
                    sender,
                    recipient,
                    subject,
                    message,
                    attachment,
                    timestamp_receive,
                    status
                FROM notif_inbox 
                WHERE recipient = ? 
                AND status = 'Read'
                ORDER BY timestamp_receive DESC
            """
			c.execute(query, (user,))

		else:  # "Inbox" - new messages
			query = """
                SELECT 
                    message_id,
                    sender,
                    recipient,
                    subject,
                    message,
                    attachment,
                    timestamp_receive,
                    status
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
	"""
	Update the message listbox with messages from the selected category
	"""
	current_user = g_recipient

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

def clear_full_message_display():
    for widget in full_message_frame.winfo_children():
        widget.destroy()

def show_full_message(event):
    selection = message_listbox.curselection()
    if not selection:
        return

    current_user = g_recipient

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

	current_user = g_recipient

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
	current_user = g_recipient

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


# Tenant side compose message UI
def compose_message():
	global compose_win, message_text

	compose_win = tk.Toplevel(root)
	compose_win.title("Compose Message")
	compose_win.geometry("800x600")
	compose_win.config(bg="#D3D3D3")

	main_frame = tk.Frame(compose_win, bg="#D3D3D3")
	main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

	main_frame.grid_columnconfigure(1, weight=1)

	# For tenants, the unit is fixed to "Admin"
	tk.Label(main_frame, text="To: Admin", font=("helvetica", 16), bg="#D3D3D3").grid(row=0, column=0, padx=10, pady=10,
	                                                                                  sticky="w")
	tk.Label(main_frame, text="Subject", font=("helvetica", 16), bg="#D3D3D3").grid(row=1, column=0, padx=10, pady=10,
	                                                                                sticky="w")
	tk.Entry(main_frame, textvariable=Subject, font=("helvetica", 16)).grid(row=1, column=1, columnspan=2, padx=10,
	                                                                        pady=10, sticky="ew")

	tk.Label(main_frame, text="Message", font=("helvetica", 16), bg="#D3D3D3").grid(row=2, column=0, padx=10, pady=10,
	                                                                                sticky="nw")
	message_text = tk.Text(main_frame, font=("helvetica", 16), width=50, height=10)
	message_text.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

	main_frame.grid_rowconfigure(2, weight=1)

	tk.Label(main_frame, text="Attachment", font=("helvetica", 16), bg="#D3D3D3").grid(row=3, column=0, padx=10,
	                                                                                   pady=10, sticky="w")
	tk.Entry(main_frame, textvariable=AttachmentPath, font=("helvetica", 16), state='readonly').grid(row=3, column=1,
	                                                                                                 padx=10, pady=10,
	                                                                                                 sticky="ew")
	tk.Button(main_frame, text="Browse", font=("helvetica", 16), command=lambda: browse_file(compose_win)).grid(row=3,
	                                                                                                            column=2,
	                                                                                                            padx=10,
	                                                                                                            pady=10,
	                                                                                                            sticky="e")

	tk.Button(main_frame, text="Send", font=("helvetica", 16), bg="#ff8210", fg="white", command=send_message).grid(
		row=4, column=1, padx=10, pady=20, sticky="ew")

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
    tk.Label(main_frame, text=f"Subject: Re: {original_subject}", font=("Helvetica", 14, "bold"), bg="#D3D3D3").pack(anchor="w")

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

tk.Label(entries_frame, text="Tenant - INBOX", font=("helvetica", 30, "bold"), bg="#F5F5F5").grid(row=0, column=0, columnspan=7,
                                                                                         padx=10, pady=20,
                                                                                         sticky="nsew")

tk.Label(entries_frame, text="Unit:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=0, padx=10, pady=10,
                                                                                 sticky="nsew")
unit_combo = ttk.Combobox(entries_frame, textvariable=Unit, font=("helvetica", 16), width=30, values=unit_set)
unit_combo.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
unit_combo.bind("<KeyRelease>", filter_units)

tk.Label(entries_frame, text="Category:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=2, padx=10, pady=10,
                                                                                     sticky="nsew")
inbox_combo = ttk.Combobox(entries_frame, textvariable=Inbox, font=("helvetica", 16), width=30, values=inbox_set)
inbox_combo.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")
inbox_combo.bind("<KeyRelease>", filter_inbox)
inbox_combo.bind("<<ComboboxSelected>>", lambda e: update_message_display())

tk.Label(entries_frame, text="Search Unit:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=4, padx=10, pady=10, sticky="nsew")
tk.Entry(entries_frame, textvariable=SearchText, font=("helvetica", 16), width=30).grid(row=1, column=5, padx=10, pady=10, sticky="nsew")
tk.Button(entries_frame, text="Search", font=("helvetica", 16), fg="white", bg="#ff8210", command=search_units).grid(row=1, column=6, padx=10, pady=10, sticky="nsew")

# Create a frame for the buttons
button_frame = tk.Frame(entries_frame, bg="#F5F5F5")
button_frame.grid(row=4, column=2, columnspan=3, padx=10, pady=10, sticky="ew")

# Configure the button frame columns
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)
button_frame.columnconfigure(2, weight=1)

# Add the buttons to the button frame
tk.Button(button_frame, text="Compose Message", font=("helvetica", 16), bg="#ff8210", fg="white", command=compose_message).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
tk.Button(button_frame, text="Delete Message", font=("helvetica", 16), bg="#ff8210", fg="white", command=delete_message).grid(row=0, column=1, padx=5, pady=5, sticky="ew")


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

full_message_frame = tk.Frame(lower_frame)
full_message_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

full_message_text = tk.Text(full_message_frame, font=("helvetica", 12), wrap=tk.WORD)
full_message_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

full_message_scrollbar = tk.Scrollbar(full_message_frame, orient=tk.VERTICAL, command=full_message_text.yview)
full_message_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
full_message_text.config(yscrollcommand=full_message_scrollbar.set)

# Initialize the message display
update_message_display()

root.mainloop()
