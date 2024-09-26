from tkinter import *
from tkinter import ttk, filedialog, messagebox

root = Tk()
root.title("Notification System")
root.geometry("1920x1080+0+0")
root.config(bg="#2c3e50")
root.state("zoomed")

Unit = StringVar()
Inbox = StringVar(value="Inbox")
SearchText = StringVar()
Subject = StringVar()
AttachmentPath = StringVar()
SendToAll = BooleanVar()
message_records = []

# List of available units
unit_set = ['Unit 101', 'Unit 202', 'Unit 303', 'Unit 304', 'Unit 305', 'Unit 306', 'Unit 401', 'Unit 402']
inbox_set = ['Inbox', 'Read', 'Sent']

# Function to filter and update the unit drop-down list
def filter_units(event):
    typed_text = Unit.get().lower()
    filtered_units = [u for u in unit_set if typed_text in u.lower()]
    unit_combo['values'] = filtered_units

# Function to filter and update the inbox drop-down list
def filter_inbox(event):
    typed_text = Inbox.get().lower()
    filtered_inbox = [i for i in inbox_set if typed_text in i.lower()]
    inbox_combo['values'] = filtered_inbox

# Function to search units based on search input
def search_units():
    search_text = SearchText.get().lower()
    filtered_units = [u for u in unit_set if search_text in u.lower()]
    result_label.config(text="Results: " + ", ".join(filtered_units))

# Function to browse and attach a file
def browse_file(window):
    file_path = filedialog.askopenfilename(title="Select file", parent=window)
    if file_path:
        AttachmentPath.set(file_path)

# Function to send message
def send_message():
    unit = "All Units" if SendToAll.get() else Unit.get()
    subject = Subject.get()
    message = message_text.get(1.0, END).strip()
    attachment = AttachmentPath.get()

    if not subject or not message:
        messagebox.showwarning("Missing Information", "Please enter both subject and message!")
        return

    # Store the message record
    message_records.append((unit, subject, message, attachment))

    # Update the message display area
    update_message_display()

    messagebox.showinfo("Message Sent", "Message sent successfully!")
    compose_win.destroy()

# Function to update the message display area
def update_message_display():
    message_listbox.delete(0, END)  # Clear previous messages
    for record in message_records:
        record_text = f"To: {record[0]}, Subject: {record[1]}, Message: {record[2]}, Attachment: {record[3] if record[3] else 'None'}"
        message_listbox.insert(END, record_text)  # Add record to Listbox

# Function to delete selected message
def delete_message():
    selected_index = message_listbox.curselection()  # Get selected index from the Listbox
    if selected_index:
        message_records.pop(selected_index[0])  # Remove the selected message from the list
        update_message_display()  # Update the Listbox display
    else:
        messagebox.showwarning("Selection Error", "Please select a message to delete.")

# Function to open a new window for composing a message
def compose_message():
    global compose_win, message_text
    compose_win = Toplevel(root)
    compose_win.title("Compose Message")
    compose_win.geometry("800x600")
    compose_win.config(bg="#D3D3D3")

    # Unit Selection
    lblUnit = Label(compose_win, text="Unit", font=("times new roman", 16), bg="#D3D3D3", fg="black")
    lblUnit.grid(row=0, column=0, padx=10, pady=10, sticky="w")

    unit_combo = ttk.Combobox(compose_win, textvariable=Unit, font=("times new roman", 16), width=30)
    unit_combo.grid(row=0, column=1, padx=10, pady=10)
    unit_combo['values'] = unit_set

    chkSendToAll = Checkbutton(compose_win, text="Send to All", variable=SendToAll, onvalue=True, offvalue=False, bg="#D3D3D3", font=("times new roman", 16))
    chkSendToAll.grid(row=0, column=2, padx=10, pady=10)

    # Subject Field
    lblSubject = Label(compose_win, text="Subject", font=("times new roman", 16), bg="#D3D3D3", fg="black")
    lblSubject.grid(row=1, column=0, padx=10, pady=10, sticky="w")
    subject_entry = Entry(compose_win, textvariable=Subject, font=("times new roman", 16), width=50)
    subject_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

    # Message Text Box
    lblMessage = Label(compose_win, text="Message", font=("times new roman", 16), bg="#D3D3D3", fg="black")
    lblMessage.grid(row=2, column=0, padx=10, pady=10, sticky="nw")
    message_text = Text(compose_win, font=("times new roman", 16), width=60, height=10)
    message_text.grid(row=2, column=1, padx=10, pady=10, sticky="w")

    # Attachment Section
    lblAttachment = Label(compose_win, text="Attachment", font=("times new roman", 16), bg="#D3D3D3", fg="black")
    lblAttachment.grid(row=3, column=0, padx=10, pady=10, sticky="w")
    attachment_entry = Entry(compose_win, textvariable=AttachmentPath, font=("times new roman", 16), width=40, state='readonly')
    attachment_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")
    browse_button = Button(compose_win, text="Browse", font=("times new roman", 16), command=lambda: browse_file(compose_win))
    browse_button.grid(row=3, column=4, padx=10, pady=10, sticky="e")

    # Send Button
    send_button = Button(compose_win, text="Send", font=("times new roman", 16), bg="green", fg="white", command=send_message)
    send_button.grid(row=5, column=1, padx=10, pady=20, sticky="nsew")

# Entries Frame
entries_frame = Frame(root, bg="#D3D3D3")
entries_frame.pack(side=TOP, fill=X)
title = Label(entries_frame, text="Notification System", font=("times new roman", 18, "bold"), bg="#D3D3D3", fg="black")
title.grid(row=0, columnspan=4, padx=10, pady=20, sticky="w")

# Unit Entry Label and Drop-Down (Combobox)
lblUnit = Label(entries_frame, text="Unit", font=("times new roman", 16), bg="#D3D3D3", fg="black")
lblUnit.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

unit_combo = ttk.Combobox(entries_frame, textvariable=Unit, font=("times new roman", 16), width=20)
unit_combo.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
unit_combo['values'] = unit_set
unit_combo.bind("<KeyRelease>", filter_units)

# Inbox Entry Label and Drop-Down (Combobox)
lblInbox = Label(entries_frame, text="Inbox", font=("times new roman", 16), bg="#D3D3D3", fg="black")
lblInbox.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

inbox_combo = ttk.Combobox(entries_frame, textvariable=Inbox, font=("times new roman", 16), width=20)
inbox_combo.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")
inbox_combo['values'] = inbox_set
inbox_combo.bind("<KeyRelease>", filter_inbox)

# Search Box for Units
lblSearch = Label(entries_frame, text="Search Unit", font=("times new roman", 16), bg="#D3D3D3", fg="black")
lblSearch.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

search_entry = Entry(entries_frame, textvariable=SearchText, font=("times new roman", 16), width=20)
search_entry.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

# Search Button
search_button = Button(entries_frame, text="Search", font=("times new roman", 16), command=search_units)
search_button.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")

# Compose Message Button
send_message_button = Button(entries_frame, text="Compose Message", font=("times new roman", 16), bg="blue", fg="white", command=compose_message)
send_message_button.grid(row=4, column=10, columnspan=3, padx=10, pady=10, sticky="nsew")

# Delete Button
delete_message_button = Button(entries_frame, text="Delete Message", font=("times new roman", 16), bg="red", fg="white", command=delete_message)
delete_message_button.grid(row=4, column=15, columnspan=3, padx=10, pady=10, sticky="nsew")

# Label to display search results
result_label = Label(entries_frame, text="Results: ", font=("times new roman", 16), bg="#D3D3D3", fg="black")
result_label.grid(row=4, column=0, columnspan=4, padx=10, pady=10, sticky="w")

# Frame to display sent messages
message_display_frame = Frame(root, bg="White", bd=2, relief=RIDGE)
message_display_frame.pack(side=TOP, fill=BOTH, expand=True, padx=10, pady=10)

# Listbox for displaying messages
message_listbox = Listbox(message_display_frame, bg="#D3D3D3", font=("times new roman", 12))
message_listbox.pack(side=LEFT, fill=BOTH, expand=True)

# Scrollbar for the message display
scrollbar = Scrollbar(message_display_frame, orient=VERTICAL, command=message_listbox.yview)
scrollbar.pack(side=RIGHT, fill=Y)

message_listbox.configure(yscrollcommand=scrollbar.set)

# Run the main loop
root.mainloop()
