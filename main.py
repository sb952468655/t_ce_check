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

        err_text =  '1、ssh\n\n' + self.config_1_name + '\n\n' + ssh(self.config) + '\n\n'
        err_text += self.config_2_name + '\n\n' + ssh(self.config2) + '\n\n\n\n\n\n'
        err_text += '2、ftp\n\n' + self.config_1_name + '\n\n' + ftp(self.config) + '\n\n'
        err_text += self.config_2_name + '\n\n' + ftp(self.config2) + '\n\n\n\n\n\n'
        err_text += '3、qos\n\n' + qos(self.config, self.config2) + '\n\n\n\n\n\n'
        err_text += '4、isis bfd\n\n' + self.config_1_name + '\n\n' + isis_bfd(self.config) + '\n\n'
        err_text += self.config_2_name + '\n\n' + isis_bfd(self.config2) + '\n\n\n\n\n\n'
        err_text += '5、static-route bfd\n\n' + self.config_1_name + '\n\n' + static_route_bfd(self.config) + '\n\n'
        err_text += self.config_2_name + '\n\n' + static_route_bfd(self.config2) + '\n\n\n\n\n\n'
        err_text += '6、bgp bfd\n\n' + self.config_1_name + '\n\n' + bgp_bfd(self.config) + '\n\n'
        err_text += self.config_2_name + '\n\n' + bgp_bfd(self.config2) + '\n\n\n\n\n\n'
        err_text += '7、policy-options\n\n' + policy_options(self.config, self.config2) + '\n\n\n\n\n\n'
        err_text += '8、路由发布对比\n\n' + policy_options_diff(self.config, self.config2) + '\n\n\n\n\n\n'
        err_text += '9、cpm-filter\n\n' + cpm_filter_check(self.config, self.config2) + '\n\n\n\n\n\n'
        err_text += '10、ip-filter 200限制\n\n' +  ip_filter_200(self.config, self.config2) + '\n\n\n\n\n\n'
        err_text += '11、垃圾静态路由检查\n\n' + self.config_1_name + ' 检查命令脚本\n\n' + vprn_static_route_check(self.config) + '\n' \
            + self.config_2_name + ' 检查命令脚本\n\n' + vprn_static_route_check(self.config2) + '\n\n\n\n\n\n'
        self.res_text.insert(tk.END, err_text)


        #窗口最大化
        root.geometry("{}x{}".format(self.w, self.h))
        root.attributes("-topmost",True)
        root.geometry("+0+0")

    def check_ce3(self):
        return os.path.exists('JS-NJ-GL-CE-3.CDMA.log')


root = tk.Tk()
root.geometry('700x380+500+200')
root.title('电信CE配置检查 V1.1.16')
# root.resizable(0,0)
myapp = App(master=root)
myapp.mainloop()