import tkinter as tk
from tkinter import ttk, filedialog
import sys
import os
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
        self.root.geometry("1000x550")
        self.root.resizable(False, False)
        self.options = [["Model", ['Default', 'Compact (experimental)', 'Physiobelt']], ["Bins", ['30 mins', '1 hour']], ["Output", ['CSV only', 'Excel only', 'CSV and Excel']], ["Markdown", ['None', 'Copy', 'Original']]]
        self.numbers = ['Channel']
        #self.options = [["No Data", "Passed", "Failed"]
        self.dictopt = {'Bins': 'half', 'SR': 0, 'verbose': 3, 'Model': 'short', 'Channel': 0, 'Rename': 0, 'Sleep': 0, 'Astronomical': 0, 'Multi': 1, 'Output': 'csvxls', 'Markdown': 'None', 'Files': [], 'Folder': os.getcwd() + '\Results'}
        #self.create_widgets()
        
    #def create_widgets(self):
        eamount = 3 #amount of stuff added after original one
        #comboboxes for lists of options
        for i, option in enumerate(self.options):
            label = tk.Label(self.root, text=option[0], bg="white")
            label.grid(row=i+eamount+1, column=2)
            var = tk.StringVar()
            combobox = ttk.Combobox(self.root, value=option[1], textvariable=var, state="readonly", width = 20)
            combobox.current(0)
            combobox.bind("<<ComboboxSelected>>", lambda event, option=option, var=var: self.update_options(option[0], var))
            combobox.grid(row=i+eamount+1, column=3)
        #numbers input
        for n, number in enumerate(self.numbers):
            label = tk.Label(self.root, text=number, bg="white")#, relief="groove")
            label.grid(row=len(self.options)+n+eamount+1, column=2)
            vcmd = self.root.register(validate_entry)
            var2 = tk.StringVar()
            entry = tk.Entry(self.root, validate='key', validatecommand=(vcmd, '%P'), textvariable=var2, width = 23, relief="solid")
            entry.insert(0, self.dictopt[number])
            entry.bind("<FocusOut>", lambda event, number=number, var=var2: self.update_numbers(number, var))
            entry.grid(row=len(self.options)+n+eamount+1, column=3)
            #HERE BE DRAGONS entry.bind("<<ComboboxSelected>>", lambda event, option=option, var=var: self.update_options(option[0], var))        rename = tk.IntVar()  
        rename = tk.IntVar()  
        sleep = tk.IntVar()
        astro = tk.IntVar()  
        marker = tk.IntVar()  
        multi = tk.IntVar() 
        rename.set(1) 
        multi.set(1) 
        #checkbutton1 = tk.Checkbutton(self.root, text="Rename folder", variable=rename, bg="white", onvalue = 1, offvalue = 0)
        #checkbutton1.grid(row=len(self.options)+n+2+eamount, column=3)
        #checkbutton1.bind("<Button-1>", lambda event, number='Rename', var=rename: self.update_checkbox(number, 1-var.get()))
        #checkbutton2 = tk.Checkbutton(self.root, text="DISABLED", variable=sleep, bg="white", onvalue = 1, offvalue = 0)
        #checkbutton2.grid(row=len(self.options)+n+2+eamount, column=3)
        #checkbutton2.bind("<Button-1>", lambda event, number='Sleep', var=sleep: self.update_checkbox(number, 1-var.get()))
        #checkbutton3 = tk.Checkbutton(self.root, text="Use astronomical time", variable=astro, bg="white", onvalue = 1, offvalue = 0)
        #checkbutton3.grid(row=len(self.options)+n+2+eamount, column=3)
        #checkbutton3.bind("<Button-1>", lambda event, number='Astronomical', var=astro: self.update_checkbox(number, 1-var.get()))
        #checkbutton4 = tk.Checkbutton(self.root, text="Add markers to EDF", variable=marker, bg="white", onvalue = 1, offvalue = 0)
        #checkbutton4.grid(row=len(self.options)+n+3+eamount, column=3)
        #checkbutton4.bind("<Button-1>", lambda event, number='Marker', var=marker: self.update_checkbox(number, 1-var.get()))
        checkbutton5 = tk.Checkbutton(self.root, text="Multiprocessing", variable=multi, bg="white", onvalue = 1, offvalue = 0)
        checkbutton5.grid(row=len(self.options)+n+2+eamount, column=3)
        checkbutton5.bind("<Button-1>", lambda event, number='Multi', var=multi: self.update_checkbox(number, 1-var.get()))

        self.lbl_selected = tk.Label(self.root, text="Output folder: " + os.getcwd() + '\Results')
        self.lbl_selected.grid(row = eamount, column = 1, rowspan = 1, padx=10, pady=10)
        global output_text
        output_text = tk.Text(self.root, height = 20, width = 80, relief="solid", state="disabled")
        output_text.grid(row = eamount+1, column = 1, rowspan = 10, padx=10, pady=10)
        #directing output here
        sys.stdout = CustomTextRedirector(output_text, "stdout")
        sys.stderr = CustomTextRedirector(output_text, "stderr")

        #button
        button_out = tk.Button(self.root, text="OUTPUT\nFOLDER", command=self.select_folder, width = 7, height = 2)
        button = tk.Button(self.root, text="START", command=lambda:butt_start(button, self.dictopt), width = 7, height = 2)
        button2 = tk.Button(self.root, text="ABOUT", command=lambda:print('DELETING WINDOWS\nPLEASE WAIT'), width = 7, height = 2)
        #button.bind("<
        button.grid(row=1, column = 3) #len(self.options)+len(self.numbers)+eamount
        button2.grid(row=2, column = 3)
        button_out.grid(row=3, column = 2)


        self.listbox = tk.Listbox(self.root, width=105, height=6, relief="solid")
        self.listbox.grid(row=1, column = 1,rowspan = 2, padx=10, pady=10)
        button_select = tk.Button(self.root, text="SELECT\nFILES", command=self.select_files, width = 7, height = 2)
        button_clear = tk.Button(self.root, text="CLEAR", command=self.clear_list, width = 7, height = 2)
        button_select.grid(row=1, column = 2)
        button_clear.grid(row=2, column = 2)

    def update_checkbox(self, number, x):
        if x != '':
            self.dictopt[number] = int(x)
        #print(self.dictopt)  # For demonstration purposes

    def update_options(self, option, var):
        # Update the archive dictionary with the selected option
        key = {'1 hour': 'hour', '30 mins': 'half', 'Physiobelt': 'physio', 'Default': 'short', 'Compact (experimental)': 'compact', 'CSV only': 'csv', 'Excel only': 'xls', 'CSV and Excel': 'csvxls', 'None': 'mrk_no',  'Copy': 'mrk_copy', 'Original': 'mrk_orig'}
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

    def select_files(self):
        files = filedialog.askopenfilenames(
            filetypes=[("European Data Format", "*.edf")])
        #self.listbox.delete(0, tk.END)
        for file in files:
            self.listbox.insert(tk.END, file)
        self.dictopt['Files'].extend(files)

    def clear_list(self):
        self.listbox.delete(0, tk.END)
        self.dictopt['Files'] = []

    def select_folder(self):
        folder = filedialog.askdirectory(title="Choose output folder:")
        if folder:
            self.lbl_selected.config(text=f"Output folder: {folder}")
            self.dictopt['Folder'] = folder
        else:
            self.lbl_selected.config(text="Output folder: " + os.getcwd() + '\Results')
            self.dictopt['Folder'] = os.getcwd() + '\Results'


def run_gui():
    root = tk.Tk()
    gui = TestReportGUI(root)
    root.mainloop()

if __name__ == '__main__':
    run_gui()
