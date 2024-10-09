import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

'''
root = tk.Tk()
root.title("Notification System")
root.geometry("1920x1080")
root.config(bg="#2c3e50")
root.state("zoomed")
'''

root = tk.Tk()
root.title("Notification System")
root.state("zoomed")  # This is already in your code, which is good

Unit = tk.StringVar()
Inbox = tk.StringVar(value="Inbox")
SearchText = tk.StringVar()
Subject = tk.StringVar()
AttachmentPath = tk.StringVar()
SendToAll = tk.BooleanVar()
message_records = []

# List of available units and inbox categories
unit_set = ['Unit 101', 'Unit 202', 'Unit 303', 'Unit 304', 'Unit 305', 'Unit 306', 'Unit 401', 'Unit 402']
inbox_set = ['Inbox', 'Read', 'Sent']

def filter_units(event):
    typed_text = Unit.get().lower()
    filtered_units = [u for u in unit_set if typed_text in u.lower()]
    unit_combo['values'] = filtered_units

def filter_inbox(event):
    typed_text = Inbox.get().lower()
    filtered_inbox = [i for i in inbox_set if typed_text in i.lower()]
    inbox_combo['values'] = filtered_inbox

def search_units():
    search_text = SearchText.get().lower()
    filtered_units = [u for u in unit_set if search_text in u.lower()]
    result_label.config(text="Results: " + ", ".join(filtered_units))

def browse_file(window):
    file_path = filedialog.askopenfilename(title="Select file", parent=window)
    if file_path:
        AttachmentPath.set(file_path)

def send_message():
    unit = "All Units" if SendToAll.get() else Unit.get()
    subject = Subject.get()
    message = message_text.get(1.0, tk.END).strip()
    attachment = AttachmentPath.get()

    if not subject or not message:
        messagebox.showwarning("Missing Information", "Please enter both subject and message!")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_records.append((unit, subject, message, attachment, timestamp, "Sent"))
    update_message_display()
    messagebox.showinfo("Message Sent", "Message sent successfully!")
    compose_win.destroy()


def update_message_display():
    message_listbox.delete(0, tk.END)
    selected_category = Inbox.get()

    for record in message_records:
        if record[5] == selected_category:
            record_text = format_record_for_listbox(record)
            message_listbox.insert(tk.END, record_text)


def format_record_for_listbox(record):
    return f"To: {record[0]} | Subject: {record[1]} | Date: {record[4]}"

def show_full_message(event):
    selection_index = message_listbox.curselection()
    if not selection_index:
        return

    selected_index = selection_index[0]
    record = message_records[selected_index]
    unit, subject, message, attachment, timestamp, status = record

    display_full_message(unit, subject, message, attachment, timestamp)

    if status == "Inbox":
        mark_message_as_read(selected_index)
def display_full_message(unit, subject, message, attachment, timestamp):
    full_message_text.delete(1.0, tk.END)
    full_message_content = f"""
To: {unit}
Subject: {subject}
Sent on: {timestamp}

Message:
{message}

Attachment: {attachment if attachment else 'None'}
    """
    full_message_text.insert(tk.END, full_message_content.strip())

def mark_message_as_read(index):
    message_records[index] = (*message_records[index][:5], "Read")
    update_message_display()

def delete_message():
    selected_index = message_listbox.curselection()
    if selected_index:
        message_records.pop(selected_index[0])
        update_message_display()
    else:
        messagebox.showwarning("Selection Error", "Please select a message to delete.")

def compose_message():
    global compose_win, message_text
    compose_win = tk.Toplevel(root)
    compose_win.title("Compose Message")
    compose_win.geometry("800x600")  # Adjust size as needed
    compose_win.config(bg="#D3D3D3")

    main_frame = tk.Frame(compose_win, bg="#D3D3D3")
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    main_frame.grid_columnconfigure(1, weight=1)

    tk.Label(main_frame, text="Unit", font=("helvetica", 16), bg="#D3D3D3").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    unit_combo = ttk.Combobox(main_frame, textvariable=Unit, font=("helvetica", 16), width=40, values=unit_set)
    unit_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    tk.Checkbutton(main_frame, text="Send to All", variable=SendToAll, bg="#D3D3D3", font=("helvetica", 16)).grid(row=0, column=2, padx=10, pady=10)

    tk.Label(main_frame, text="Subject", font=("helvetica", 16), bg="#D3D3D3").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    tk.Entry(main_frame, textvariable=Subject, font=("helvetica", 16)).grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

    tk.Label(main_frame, text="Message", font=("helvetica", 16), bg="#D3D3D3").grid(row=2, column=0, padx=10, pady=10, sticky="nw")
    message_text = tk.Text(main_frame, font=("helvetica", 16), width=50, height=10)
    message_text.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

    main_frame.grid_rowconfigure(2, weight=1)

    tk.Label(main_frame, text="Attachment", font=("helvetica", 16), bg="#D3D3D3").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    tk.Entry(main_frame, textvariable=AttachmentPath, font=("helvetica", 16), state='readonly').grid(row=3, column=1, padx=10, pady=10, sticky="ew")
    tk.Button(main_frame, text="Browse", font=("helvetica", 16), command=lambda: browse_file(compose_win)).grid(row=3, column=2, padx=10, pady=10, sticky="e")

    tk.Button(main_frame, text="Send", font=("helvetica", 16), bg="#ff8210", fg="white", command=send_message).grid(row=4, column=1, padx=10, pady=20, sticky="ew")


def reply_message():
    # Get the selected message from the listbox
    selection_index = message_listbox.curselection()
    if not selection_index:
        messagebox.showwarning("Selection Error", "Please select a message to reply to.")
        return

    selected_index = selection_index[0]
    record = message_records[selected_index]
    unit, subject, message, attachment, timestamp, status = record

    # Open a new compose window for the reply
    global compose_win, message_text
    compose_win = tk.Toplevel(root)
    compose_win.title("Reply Message")
    compose_win.geometry("800x600")
    compose_win.config(bg="#D3D3D3")

    main_frame = tk.Frame(compose_win, bg="#D3D3D3")
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
    main_frame.grid_columnconfigure(1, weight=1)

    tk.Label(main_frame, text="To", font=("helvetica", 16), bg="#D3D3D3").grid(row=0, column=0, padx=10, pady=10,
                                                                               sticky="w")
    unit_entry = ttk.Combobox(main_frame, textvariable=Unit, font=("helvetica", 16), width=40, values=[unit])
    unit_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    unit_entry.set(unit)  # Set the "To" field with the original sender

    tk.Label(main_frame, text="Subject", font=("helvetica", 16), bg="#D3D3D3").grid(row=1, column=0, padx=10, pady=10,
                                                                                    sticky="w")
    subject_entry = tk.Entry(main_frame, textvariable=Subject, font=("helvetica", 16))
    subject_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
    subject_entry.insert(0, f"Re: {subject}")  # Prepend "Re: " to the original subject

    tk.Label(main_frame, text="Message", font=("helvetica", 16), bg="#D3D3D3").grid(row=2, column=0, padx=10, pady=10,
                                                                                    sticky="nw")
    message_text = tk.Text(main_frame, font=("helvetica", 16), width=50, height=10)
    message_text.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

    main_frame.grid_rowconfigure(2, weight=1)

    tk.Button(main_frame, text="Send Reply", font=("helvetica", 16), bg="#5e9918", fg="white",
              command=send_message).grid(row=4, column=1, padx=10, pady=20, sticky="ew")
# -------------------------Main UI setup---------------------------------
# Configure the frame
entries_frame = tk.Frame(root, bg="#F5F5F5")
entries_frame.pack(side=tk.TOP, fill=tk.X)

# Configure the grid columns to expand evenly
entries_frame.grid_columnconfigure(0, weight=1)
entries_frame.grid_columnconfigure(1, weight=1)
entries_frame.grid_columnconfigure(2, weight=1)
entries_frame.grid_columnconfigure(3, weight=1)
entries_frame.grid_columnconfigure(4, weight=1)
entries_frame.grid_columnconfigure(5, weight=1)
entries_frame.grid_columnconfigure(6, weight=1)

# Add widgets
tk.Label(entries_frame, text="INBOX", font=("helvetica", 30, "bold"), bg="#F5F5F5").grid(row=0, column=0, columnspan=7, padx=10, pady=20, sticky="nsew")

tk.Label(entries_frame, text="Unit:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
unit_combo = ttk.Combobox(entries_frame, textvariable=Unit, font=("helvetica", 16), width=30, values=unit_set)
unit_combo.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
unit_combo.bind("<KeyRelease>", filter_units)

tk.Label(entries_frame, text="Category:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=2, padx=10, pady=10, sticky="nsew")
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

# Add the buttons to the button frame
tk.Button(button_frame, text="Compose Message", font=("helvetica", 16), bg="#ff8210", fg="white", command=compose_message).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
tk.Button(button_frame, text="Delete Message", font=("helvetica", 16), bg="#ff8210", fg="white", command=delete_message).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
tk.Button(button_frame, text="Reply", font=("helvetica", 16), bg="#ff8210", fg="white", command=reply_message).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

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

root.mainloop()