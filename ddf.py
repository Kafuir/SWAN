import tkinter as tk
from tkinter import ttk
import sys
import SWD
import threading

def validate_entry(text):
    # Allow the entry if the text is decimal (i.e., contains only digits)
    return (text.isdigit() or text == '') #'' is used to allow deleting the last number

def make_thread(key):
    threading.Thread(target=SWD.launch, args = (key,)).start()
    #p = Process(target=SWD.launch, args=(key,))
    #p.start()
    
def butt_start(button, key):
    # This function will be called when the button is clicked
    button.config(state=tk.DISABLED, relief="sunken")
    make_thread(key)
    button.config(state=tk.NORMAL, relief="raised")

class CustomTextRedirector:
    #this deep dark magic redirects print's to output of the gui
    def __init__(self, text_widget, tag="stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, msg):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, msg, (self.tag,))
        self.text_widget.configure(state="disabled")
        # Automatically scroll to the bottom
        self.text_widget.see(tk.END)

    def flush(self):
        pass  # Needed for file-like object but not actually used here



class TestReportGUI:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg="white")
        self.root.title("SWAN")
        self.root.geometry("550x200")
        self.root.resizable(False, False)
        self.options = [["Model", ['Default', 'Compact (experimental)']], ["Bins", ['30 mins', '1 hour']]]
        self.numbers = ['SR', 'Channel']
        #self.options = [["No Data", "Passed", "Failed"]
        self.dictopt = {'Bins': 'half', 'SR': 400, 'verbose': 3, 'Model': 'short', 'Channel': 0}
        self.create_widgets()
        
    def create_widgets(self):
        #comboboxes for lists of options
        for i, option in enumerate(self.options):
            print(i)
            label = tk.Label(self.root, text=option[0], bg="white")
            label.grid(row=i, column=2)
            var = tk.StringVar()
            combobox = ttk.Combobox(self.root, value=option[1], textvariable=var, state="readonly", width = 20)
            combobox.current(0)
            combobox.bind("<<ComboboxSelected>>", lambda event, option=option, var=var: self.update_options(option[0], var))
            combobox.grid(row=i, column=3)
        #numbers input
        for n, number in enumerate(self.numbers):
            label = tk.Label(self.root, text=number, bg="white")#, relief="groove")
            label.grid(row=len(self.options)+n, column=2)
            vcmd = self.root.register(validate_entry)
            var2 = tk.StringVar()
            entry = tk.Entry(self.root, validate='key', validatecommand=(vcmd, '%P'), textvariable=var2, width = 23, relief="solid")
            entry.insert(0, self.dictopt[number])
            entry.bind("<FocusOut>", lambda event, number=number, var=var2: self.update_numbers(number, var))
            entry.grid(row=len(self.options)+n, column=3)
            #HERE BE DRAGONS entry.bind("<<ComboboxSelected>>", lambda event, option=option, var=var: self.update_options(option[0], var))
        
        global output_text
        output_text = tk.Text(self.root, height = 10, width = 40, relief="solid", state="disabled")
        output_text.grid(row = 0, column = 1, rowspan = 5, padx=10, pady=10)
        #directing output here
        sys.stdout = CustomTextRedirector(output_text, "stdout")
        sys.stderr = CustomTextRedirector(output_text, "stderr")

        #button
        
        button = tk.Button(self.root, text="START", command=lambda:butt_start(button, self.dictopt))
        #button.bind("<
        button.grid(row=len(self.options)+len(self.numbers), column = 3)
        print ('')


    def update_options(self, option, var):
        # Update the archive dictionary with the selected option
        key = {'1 hour': 'hour', '30 mins': 'half', 'Short': 'short', 'Compact (experimental)': 'compact'}
        x = var.get()
        if x in key:
            x = key[x]
        self.dictopt[option] = x
        #print(self.dictopt)  # For demonstration purposes

    def update_numbers(self, number, var):
        x = var.get()
        if x != '':
            self.dictopt[number] = int(x)
        #print(self.dictopt)  # For demonstration purposes

    def print_to_text_widget(message):
        output_text.insert(tk.END, message + "\n")
        output_text.see(tk.END)


def run_gui():
    root = tk.Tk()
    gui = TestReportGUI(root)
    root.mainloop()

run_gui()
