# encoding = utf-8
import tkinter as tk
import tkinter.messagebox as msg
import tkinter.filedialog as filedialog
from check import *
import os

class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.config = None
        self.config2 = None

        self.w = self.winfo_screenwidth()
        self.h = self.winfo_screenheight()

        self.pack()
        self.create_win()


    def create_win(self):
        f1 = tk.Frame(self)
        self.import1_btn = tk.Button(f1, text='导入设备1配置', command=self.import_config)
        self.import1_btn.pack(side=tk.LEFT)
        self.import2_btn = tk.Button(f1, text='导入设备2配置', command=self.import2)
        self.import2_btn.pack(side=tk.LEFT)
        self.check_btn = tk.Button(f1, text='检查', command=self.check)
        self.check_btn.pack(side=tk.LEFT)
        self.export_btn = tk.Button(f1, text='导出检查结果', command=self.export)
        self.export_btn.pack(side=tk.LEFT)
        f1.pack()

        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.res_text = tk.Text(self, width='300',height= '{}'.format(self.h), borderwidth='2', yscrollcommand=self.scrollbar.set)
       
        self.res_text.pack()
        self.scrollbar.config(command=self.res_text.yview)


    def import_config(self):
        self.filename = filedialog.askopenfilename()
        self.res_text.delete(0.0,tk.END)
        #读取配置
        f = open(self.filename)
        try:
            self.config = f.read()
            self.config_1_name = get_host_name(self.config)
        except UnicodeDecodeError:
            msg.showerror('错误', '配置1编码错误，编码必须为UTF-8')
            self.config = None
            
        f.close()

    def import2(self):
        self.filename2 = filedialog.askopenfilename()
        self.res_text.delete(0.0,tk.END)
        #读取配置
        f = open(self.filename2)
        try:
            self.config2 = f.read()
            self.config_2_name = get_host_name(self.config2)
        except UnicodeDecodeError:
            msg.showerror('错误', '配置2编码错误，编码必须为UTF-8')
            self.config2 = None

        f.close()

    def export(self):
        '''导出检查结果'''

        file_path = os.path.join('检查结果', '{}和{}'.format(self.config_1_name, self.config_2_name))
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        self.save_name = os.path.join(file_path, '{}与{}检查结果.log'.format(self.config_1_name, self.config_2_name))
        with open(self.save_name, 'w', encoding='utf-8') as f:
            f.write(self.res_text.get("0.0", "end"))

        msg.showinfo('提示', '保存成功请在 {} 目录查看'.format(os.path.join(os.getcwd(),file_path + '\\')))

    def check(self):
        if self.config == None:
            msg.showerror('错误', '请导入设备1配置')
            return
        if self.config2 == None:
            msg.showerror('错误', '请导入设备2配置')
            return

        if not self.check_ce3():
            msg.showerror('错误', 'JS-NJ-GL-CE-3.CDMA.log文件不存在，请检查')
            return

        err_text = all_check(self.config, self.config2)
        self.res_text.insert(tk.END, err_text)


        #窗口最大化
        root.geometry("{}x{}".format(self.w, self.h))
        root.attributes("-topmost",True)
        root.geometry("+0+0")

    def check_ce3(self):
        return os.path.exists('JS-NJ-GL-CE-3.CDMA.log')


root = tk.Tk()
root.geometry('700x380+500+200')
root.title('电信CE配置检查 V1.1.24')
# root.resizable(0,0)
myapp = App(master=root)
myapp.mainloop()