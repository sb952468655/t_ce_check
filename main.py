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
        self.kind = tk.StringVar(f1)
        self.kind.set("CE配置静态检查")
        self.op = tk.OptionMenu(f1, self.kind, 'CE配置静态检查', '垃圾静态路由检查', '成对CE路由发布对比')
        self.op.pack(side=tk.LEFT)
        self.import1_btn = tk.Button(f1, text='导入设备1配置', command=self.import_config)
        # self.import1_btn.bind("<Button-1>", self.callBack)
        self.import1_btn.pack(side=tk.LEFT)
        self.import2_btn = tk.Button(f1, text='导入设备2配置', command=self.import2)
        # self.import2_btn.pack(side=tk.LEFT)
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

    def callBack(self, event):
        if self.kind.get() == '成对CE路由发布对比':
            self.import2_btn.pack(side=tk.LEFT)
        else:
            self.import2_btn.pack_forget()
        self.import_config()

    def import_config(self):
        if self.kind.get() == '成对CE路由发布对比':
            self.import2_btn.pack(side=tk.LEFT)
        else:
            self.import2_btn.pack_forget()

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
        save_file = filedialog.asksaveasfilename()
        if save_file:
            f = open(save_file, 'w')
            f.write(self.res_text.get(0.0, tk.END))
            f.close()

    def check(self):
        err = ''
        if self.config == None:
            msg.showerror('错误', '请导入设备1配置')
            return

        if not self.check_ce3():
            msg.showerror('错误', 'JS-NJ-GL-CE-3.CDMA.log文件不存在，请检查')
            return

        check_kind = self.kind.get()
        if check_kind == 'CE配置静态检查':
            err = static_config_check(self.config)
        elif check_kind == '垃圾静态路由检查':
            if self.config2 == None:
                msg.showerror('错误', '请导入设备2配置')
                return
        else:
            # err = all_check(self.config, self.config2)
            pass
        self.res_text.insert(tk.END, err)

        #窗口最大化
        root.geometry("{}x{}".format(self.w, self.h))
        root.attributes("-topmost",True)
        root.geometry("+0+0")

    def check_ce3(self):
        return os.path.exists('JS-NJ-GL-CE-3.CDMA.log')


root = tk.Tk()
root.geometry('700x380+500+200')
root.title('电信CE配置检查 V1.1.26')
# root.resizable(0,0)
myapp = App(master=root)
myapp.mainloop()