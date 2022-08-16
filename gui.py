import tkinter as tk

class MainWindow:
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)

        # Add button
        self.add_button = tk.Button(self.frame, text = 'Add', width = 25, command = self.add_person)
        self.add_button.pack()

        # Exit button
        self.exit_button = tk.Button(self.frame, text = 'Exit', width = 25, command = self.close_windows)
        self.exit_button.pack()

        self.frame.pack()

    def add_person(self):
        pass

    def close_windows(self):
        self.master.destroy()

def main(): 
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == '__main__':
    main()