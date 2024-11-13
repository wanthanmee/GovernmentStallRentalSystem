import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import sqlite3
import datetime
import uuid
import os
import shutil

# Modify the existing root = tk.Tk() section to include setting the current tenant
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

current_tenant_id = None  # Will store the current tenant's ID
def set_current_tenant(tenant_id):
    """Set the current tenant ID for the session"""
    global current_tenant_id
    current_tenant_id = tenant_id


# List of available units and inbox categories
inbox_set = ['Inbox', 'Read', 'Sent']

def create_database_tables():
    conn = sqlite3.connect('db_messages6.db')
    c = conn.cursor()

    try:
        # Create notif_sent_reply table
        c.execute("""
            CREATE TABLE IF NOT EXISTS notif_sent_reply (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                attachment TEXT,
                timestamp_sent_reply DATETIME NOT NULL,
                status TEXT DEFAULT 'Sent'
            )
        """)

        # Create notif_inbox table
        c.execute("""
            CREATE TABLE IF NOT EXISTS notif_inbox (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                attachment TEXT,
                timestamp_receive DATETIME NOT NULL,
                status TEXT NOT NULL DEFAULT 'New'
            )
        """)

        conn.commit()

    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
    finally:
        conn.close()

# Call this function at the start of your program
if __name__ == "__main__":
    create_database_tables()
    # Your existing main code...
def generate_message_id():
	"""Generate a unique message ID"""
	return str(uuid.uuid4())

def filter_inbox(event):
	typed_text = Inbox.get().lower()
	filtered_inbox = [i for i in inbox_set if typed_text in i.lower()]
	inbox_combo['values'] = filtered_inbox

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

def Tenant_ID():
    conn = sqlite3.connect('govRental.db')
    c = conn.cursor()

    try:
        c.execute("SELECT DISTINCT Tenant_ID FROM Tenant")
        postcodes = [row[0] for row in c.fetchall()]
        return postcodes
    finally:
        conn.close()  # Ensure connection is closed after fetching

def Tenant_Username():
	conn = sqlite3.connect('govRental.db')
	c = conn.cursor()

	try:
		c.execute("SELECT DISTINCT Tenant_Username FROM Tenant")
		stall_id = [row[0] for row in c.fetchall()]
		return stall_id
	finally:
		conn.close()  # Ensure connection is closed after fetching


def insert_message_to_tables(sender, recipient, subject, message, attachment=None):
    """Insert message into both notif_sent_reply and notif_inbox tables"""
    conn = sqlite3.connect('db_messages6.db')
    c = conn.cursor()

    try:
        # Generate a unique message ID
        message_id = generate_message_id()
        print(f"Generated message_id: {message_id}")  # Log the generated ID

        # Validate input parameters
        if not all([sender, recipient, subject, message]):
            raise ValueError("Sender, recipient, subject, and message must not be empty.")

        # Insert into notif_sent_reply table
        c.execute(''' 
            INSERT INTO notif_sent_reply (
                message_id, sender, recipient, subject, message, attachment, timestamp_sent_reply
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (message_id, sender, recipient, subject, message, attachment))

        # Insert into notif_inbox table with 'New' status
        c.execute(''' 
            INSERT INTO notif_inbox (
                message_id, sender, recipient, subject, message, attachment, 
                timestamp_receive, timestamp_read, status
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, NULL, 'New')
        ''', (message_id, sender, recipient, subject, message, attachment))

        # Commit the transaction
        conn.commit()

        # Print the inserted message ID
        print(f"Inserted message into notif_sent_reply with ID: {message_id}")
        print(f"Inserted message into notif_inbox with ID: {message_id}")

        return True

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False
    except ValueError as ve:
        print(f"Input validation error: {ve}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        conn.close()

# Set the current tenant ID when the application starts
set_current_tenant(Tenant_ID)  # Using the existing Tenant_ID variable
Tenant_ID = 1

import time

def generate_message_id():
    """Generate a unique message ID using the current timestamp."""
    return str(int(time.time() * 1000))  # Using timestamp as a unique ID

def send_message(Tenant_ID):
    # Retrieve the values from the Subject and Message fields
    subject = Subject.get()
    message = message_text.get("1.0", tk.END).strip()

    # Validate inputs
    if not subject or not message:
        tk.messagebox.showwarning("Input Error", "Please fill in both the subject and message fields.")
        return

    try:
        # Generate a unique message_id
        message_id = generate_message_id()
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect('db_messages6.db')
        c = conn.cursor()

        # Save attachment if provided
        attachment_path = AttachmentPath.get()
        if attachment_path:
            saved_attachment = save_attachment(attachment_path)
        else:
            saved_attachment = None

        # Insert into notif_sent_reply table
        c.execute("""
            INSERT INTO notif_sent_reply (
                message_id, sender, recipient, subject, message, 
                attachment, timestamp_sent_reply
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (message_id, str(Tenant_ID), 'Admin', subject, message, saved_attachment, current_timestamp))

        # Insert into notif_inbox table with 'New' status
        c.execute("""
            INSERT INTO notif_inbox (
                message_id, sender, recipient, subject, message,
                attachment, timestamp_receive, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'New')
        """, (message_id, str(Tenant_ID), 'Admin', subject, message, saved_attachment, current_timestamp))

        conn.commit()
        conn.close()

        # Update the message display
        update_message_display()

        # Show success message and close compose window
        tk.messagebox.showinfo("Success", "Message sent successfully!")
        compose_win.destroy()

    except Exception as e:
        print(f"Error sending message: {str(e)}")
        tk.messagebox.showerror("Error", f"Failed to send message: {str(e)}")


def compose_message(Tenant_ID):
    global compose_win, message_text

    compose_win = tk.Toplevel(root)
    compose_win.title("Compose Message")
    compose_win.geometry("800x600")
    compose_win.config(bg="#D3D3D3")

    main_frame = tk.Frame(compose_win, bg="#D3D3D3")
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    main_frame.grid_columnconfigure(1, weight=1)

    # For tenants, the unit is fixed to "Admin"
    tk.Label(main_frame, text="To: Admin", font=("helvetica", 16), bg="#D3D3D3").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    tk.Label(main_frame, text="Subject", font=("helvetica", 16), bg="#D3D3D3").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    tk.Entry(main_frame, textvariable=Subject, font=("helvetica", 16)).grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

    tk.Label(main_frame, text="Message", font=("helvetica", 16), bg="#D3D3D3").grid(row=2, column=0, padx=10, pady=10, sticky="nw")
    message_text = tk.Text(main_frame, font=("helvetica", 16), width=50, height=10)
    message_text.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

    main_frame.grid_rowconfigure(2, weight=1)

    tk.Label(main_frame, text="Attachment", font=("helvetica", 16), bg="#D3D3D3").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    tk.Entry(main_frame, textvariable=AttachmentPath, font=("helvetica", 16), state='readonly').grid(row=3, column=1, padx=10, pady=10, sticky="ew")
    tk.Button(main_frame, text="Browse", font=("helvetica", 16), command=lambda: browse_file(compose_win)).grid(row=3, column=2, padx=10, pady=10, sticky="e")

    # Use lambda to ensure Tenant_ID is passed to send_message
    tk.Button(main_frame, text="Send", font=("helvetica", 16), bg="#ff8210", fg="white", command=lambda: send_message(Tenant_ID)).grid(row=4, column=1, padx=10, pady=20, sticky="ew")


def get_messages(tenant_id, category, message_id=None):
    print(f"Fetching messages for message_id: {message_id} in category: {category}")
    conn = sqlite3.connect('db_messages6.db')
    c = conn.cursor()

    if category == "Sent":
        if message_id:
            query = """SELECT message_id, sender, recipient, subject, message, attachment, timestamp_sent_reply
                       FROM notif_sent_reply WHERE message_id = ?"""
            c.execute(query, (message_id,))
        else:
            query = """SELECT message_id, sender, recipient, subject, message, attachment, timestamp_sent_reply
                       FROM notif_sent_reply WHERE sender = ?"""
            c.execute(query, (tenant_id,))
    elif category == "Inbox":
        if message_id:
            query = """SELECT message_id, sender, recipient, subject, message, attachment, timestamp_receive, status
                       FROM notif_inbox WHERE message_id = ?"""
            c.execute(query, (message_id,))
        else:
            query = """SELECT message_id, sender, recipient, subject, message, attachment, timestamp_receive, status
                       FROM notif_inbox WHERE recipient = ?"""
            c.execute(query, (tenant_id,))
    else:
        print("Unknown category:", category)
        return []

    messages = c.fetchall()
    conn.close()

    print(f"Fetched {len(messages)} messages")
    for msg in messages:
        print(msg)

    return messages

def update_message_display(tenant_id_filter=None):
    message_listbox.delete(0, tk.END)
    selected_category = Inbox.get()
    messages = get_messages(Tenant_ID, selected_category)

    if tenant_id_filter:
        messages = [msg for msg in messages if msg[1] == tenant_id_filter]

    for message in messages:
        if selected_category == "Sent":
            message_id, sender, recipient, subject, message_text, attachment, timestamp = message
            status = "Sent"  # For sent messages, status is always "Sent"
        else:
            message_id, sender, recipient, subject, message_text, attachment, timestamp, status = message

        # Format timestamp for display
        try:
            timestamp_obj = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            formatted_date = timestamp_obj.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            formatted_date = "Unknown date"

        # Create display text based on category
        if selected_category == "Sent":
            display_text = f"To: {recipient} | Subject: {subject} | Date: {formatted_date}"
        else:
            display_text = f"From: {sender} | Subject: {subject} | Date: {formatted_date}"

        # Add attachment indicator if present
        if attachment:
            display_text += " 📎"

        message_listbox.insert(tk.END, display_text)

        # Set background color for new messages
        if selected_category == "Inbox" and status == 'New':
            message_listbox.itemconfig(message_listbox.size() - 1, {'bg': '#FFE4B5'})  # Light orange background

def show_full_message(event):
    selection = message_listbox.curselection()
    if not selection:
        return

    selected_index = selection[0]
    selected_category = Inbox.get()

    # Get the full listbox entry text
    selected_text = message_listbox.get(selected_index)

    # Find the message in the current messages list that matches the displayed text
    messages = get_messages(Tenant_ID, selected_category)

    # Find the matching message from our messages list
    matching_message = None
    for msg in messages:
        # Reconstruct the display text for comparison
        if selected_category == "Sent":
            message_id, sender, recipient, subject, _, _, timestamp = msg
            display_text = f"To: {recipient} | Subject: {subject} | Date: {timestamp}"
        else:
            message_id, sender, recipient, subject, _, _, timestamp, _ = msg
            display_text = f"From: {sender} | Subject: {subject} | Date: {timestamp}"

        if selected_text.startswith(display_text.split(" | Date:")[0]):  # Compare without exact timestamp match
            matching_message = msg
            break

    if not matching_message:
        messagebox.showwarning("No Messages", "There are no messages to display.")
        return

    # Get the full message details using the message_id
    message_id = matching_message[0]  # First element is message_id
    full_message = get_messages(Tenant_ID, selected_category, message_id=message_id)

    if not full_message:
        messagebox.showwarning("No Messages", "There are no messages to display.")
        return

    # Rest of your existing show_full_message code remains the same
    if len(full_message) == 1:
        # Unpack the message details based on the selected category
        if selected_category == "Sent":
            message_id, sender, recipient, subject, message, attachment, timestamp = full_message[0]
            status = "Sent"
        else:
            message_id, sender, recipient, subject, message, attachment, timestamp, status = full_message[0]

        # Clear previous content and display the message details
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
                sender=Tenant_ID,
                recipient=sender,
                subject=f"Re: {subject.replace('Re: ', '')}",
                reply_message=reply_text.get("1.0", tk.END).strip(),
                original_message_id=message_id,
                reply_text=reply_text
            )
        )
        reply_button.pack(side=tk.RIGHT)

        # Mark the message as read
        mark_message_as_read(message_id)

def mark_message_as_read(message_id):
    """
    Mark a message as read in the notif_inbox table
    """
    if current_tenant_id is None:
        print("Warning: No current tenant ID set")
        return

    conn = sqlite3.connect('db_messages6.db')
    c = conn.cursor()

    try:
        # First check if the message is in 'New' status
        c.execute("""
            SELECT status 
            FROM notif_inbox 
            WHERE message_id = ? AND recipient = ? AND status = 'New'
        """, (message_id, str(current_tenant_id)))

        if c.fetchone():  # Only update if message is in 'New' status
            current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                UPDATE notif_inbox 
                SET status = 'Read', timestamp_read = ? 
                WHERE message_id = ? AND recipient = ? AND status = 'New'
            """, (current_timestamp, message_id, str(current_tenant_id)))
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
	current_user = Tenant_ID

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
    if not reply_message:
        messagebox.showwarning("Empty Reply", "Please enter a reply message.")
        return

    try:
        conn = sqlite3.connect('db_messages6.db')
        c = conn.cursor()
        
        # Generate a new message_id for the reply
        new_message_id = generate_message_id()
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # First get the original message thread
        c.execute("""
            SELECT message FROM notif_sent_reply 
            WHERE message_id = ?
        """, (original_message_id,))
        result = c.fetchone()
        
        if result:
            original_message = result[0]
            # Create the updated message thread content
            updated_message = f"{original_message}\n--- Reply from {sender} ---\n{current_timestamp}: {reply_message}"
        else:
            # If original message not found, just use the reply
            updated_message = reply_message

        # Begin transaction
        conn.execute('BEGIN')

        # Insert into notif_sent_reply first (parent table)
        c.execute("""
            INSERT INTO notif_sent_reply (
                message_id, sender, recipient, subject, message, 
                attachment, timestamp_sent_reply
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (new_message_id, sender, recipient, subject, updated_message, None, current_timestamp))

        # Then insert into notif_inbox (child table)
        c.execute("""
            INSERT INTO notif_inbox (
                message_id, sender, recipient, subject, message,
                attachment, timestamp_receive, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_message_id, sender, recipient, subject, updated_message, None, current_timestamp, 'New'))

        conn.commit()

        # Clear the reply text box
        reply_text.delete("1.0", tk.END)

        # Refresh the full message display to include the new reply
        show_full_message(None)

        messagebox.showinfo("Reply Sent", "Your reply has been sent successfully!")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error: {e}. Error details: {e.args}")
        messagebox.showerror("Error", "Failed to send reply.")
    finally:
        conn.close()


# Main UI setup
entries_frame = tk.Frame(root, bg="#F5F5F5")
entries_frame.pack(side=tk.TOP, fill=tk.X)

for i in range(7):
	entries_frame.grid_columnconfigure(i, weight=1)

tk.Label(entries_frame, text="Tenant - INBOX", font=("helvetica", 30, "bold"), bg="#F5F5F5").grid(row=0, column=0, columnspan=7,
                                                                                         padx=10, pady=20,
                                                                                         sticky="nsew")


tk.Label(entries_frame, text="Category:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=2, padx=10, pady=10,
                                                                                     sticky="nsew")
inbox_combo = ttk.Combobox(entries_frame, textvariable=Inbox, font=("helvetica", 16), width=30, values=inbox_set)
inbox_combo.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")
inbox_combo.bind("<KeyRelease>", filter_inbox)
inbox_combo.bind("<<ComboboxSelected>>", lambda e: update_message_display())


# Create a frame for the buttons
button_frame = tk.Frame(entries_frame, bg="#F5F5F5")
button_frame.grid(row=4, column=2, columnspan=3, padx=10, pady=10, sticky="ew")

# Configure the button frame columns
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)
button_frame.columnconfigure(2, weight=1)

# Add the buttons to the button frame
tk.Button(
    button_frame,
    text="Compose Message",
    font=("helvetica", 16),
    bg="#ff8210",
    fg="white",
    command=lambda: compose_message(Tenant_ID)  # Pass Tenant_id here
).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
tk.Button(button_frame, text="Delete Message", font=("helvetica", 16), bg="#ff8210", fg="white", command=delete_message).grid(row=0, column=1, padx=5, pady=5, sticky="ew")


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



root.mainloop()