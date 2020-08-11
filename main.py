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
        self.f1 = tk.Frame(self)
        self.kind = tk.StringVar(self.f1)
        self.kind.set("CE配置静态检查")
        self.op = tk.OptionMenu(self.f1, self.kind, 'CE配置静态检查', '垃圾静态路由检查', '成对CE路由发布对比')
        self.op.pack(side=tk.LEFT)
        self.import1_btn = tk.Button(self.f1, text='导入设备1配置', command=self.import_config)
        self.import1_btn.pack(side=tk.LEFT)
        self.import2_btn = tk.Button(self.f1, text='导入设备2配置', command=self.import2)
        # self.import2_btn.pack(side=tk.LEFT)
        self.check_btn = tk.Button(self.f1, text='检查', command=self.check)
        self.check_btn.pack(side=tk.LEFT)
        self.export_btn = tk.Button(self.f1, text='导出检查结果', command=self.export)
        self.export_btn.pack(side=tk.LEFT)
        self.import_ce_log_btn = tk.Button(self.f1, text='导入CE检查log', command=self.import_ce_log)
        self.ce_check_btn = tk.Button(self.f1, text='检查', command=self.ce_check)
        self.f1.pack()

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
            self.sort_btn('成对CE路由发布对比')
        elif self.kind.get() == '垃圾静态路由检查':
            self.sort_btn('垃圾静态路由检查')
        else:
            self.sort_btn('CE配置静态检查')

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

    def import_ce_log(self):
        '''导入CE检查log（用户使用上步骤的脚本在设备上执行产生的log）'''

        self.filename = filedialog.askopenfilename()
        self.res_text.delete(0.0,tk.END)
        #读取配置
        f = open(self.filename)
        try:
            self.ce_check_log = f.read()
        except UnicodeDecodeError:
            msg.showerror('错误', '配置1编码错误，编码必须为UTF-8')
            self.ce_check_log = None
            
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
            if self.kind.get() == '成对CE路由发布对比':
                f.write(self.config + '\n\n' + self.config2)
            elif self.kind.get() == '垃圾静态路由检查':
                f.write(self.ce_static_route_config)
            else:
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
            err = vprn_static_route_check(self.config)
        else:
            if self.config2 == None:
                msg.showerror('错误', '请导入设备2配置')
                return
            err, config1, config2 = policy_options_diff(self.config, self.config2)
            self.config = config1
            self.config2 = config2
        self.res_text.insert(tk.END, err)

        #窗口最大化
        root.geometry("{}x{}".format(self.w, self.h))
        root.attributes("-topmost",True)
        root.geometry("+0+0")

    def ce_check(self):
        '''CE垃圾静态路由检查'''

        #三种情况要提示
        #1.ping不通
        #2.show router xx route-table x.x.x.x结果为空的
        #3.show router xx route-table x.x.x.x下一跳为(tunneled) 
        err = ''

        self.ce_static_route_config = self.config
        # p = r'(?s)(show router (\d{1,9}) route-table (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}) ?\n={79}.*?\n={79}.*?\n={79})'
        p = r'(?s)(show router (\d{1,9}) route-table (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}).*?AC7750)'
        res = re.findall(p, self.ce_check_log)
        for i in res:
            is_err = True
            if '100% packet loss' in i[0]:
                err += 'router {} route-table {} ping不通\n'.format(i[1], i[2])
            elif 'No. of Routes: 0' in i[0]:
                err += 'router {} route-table {} 结果为空\n'.format(i[1], i[2])
            elif 'tunneled' in i[0]:
                err += 'router {} route-table {} 下一跳为(tunneled)\n'.format(i[1], i[2])
            else:
                is_err = False

            if is_err:
                p_static_route_entry = r'(?s)(            static-route-entry %s.*?\n {12}exit)' % i[2]
                res_static_route_entry = re.search(p_static_route_entry, self.config)
                if res_static_route_entry:
                    str_spt = res_static_route_entry.group().split('\n')
                    flag_str = ''
                    for j in str_spt:
                        flag_str += '-?' + j + '\n'
                    self.ce_static_route_config = self.ce_static_route_config.replace(res_static_route_entry.group(), '请人工再次确认{}路由是否是垃圾静态路由！\n'.format(i[2]) + flag_str)


        #原配置添加错误提示

        self.res_text.insert(tk.END, err)

    def check_ce3(self):
        return os.path.exists('JS-NJ-GL-CE-3.CDMA.log')

    def generate_config(self):
        '''CE垃圾静态路由检查'''

        err = ''
        if self.config == None:
            msg.showerror('错误', '请导入设备1配置')
            return

        err = vprn_static_route_check(self.config)
        self.res_text.insert(tk.END, err)

        #窗口最大化
        root.geometry("{}x{}".format(self.w, self.h))
        root.attributes("-topmost",True)
        root.geometry("+0+0")

    def sort_btn(self, check_type):
        '''重新排列按钮'''
        self.f1.place_forget()
        if check_type == 'CE配置静态检查':
            self.import2_btn.pack_forget()
            self.import_ce_log_btn.pack_forget()
            self.ce_check_btn.pack_forget()
            self.check_btn['text'] = '检查'
        elif check_type == '垃圾静态路由检查':
            self.check_btn.pack_forget()
            self.import2_btn.pack_forget()
            self.import_ce_log_btn.pack_forget()
            self.ce_check_btn.pack_forget()
            self.export_btn.pack_forget()
            self.import_ce_log_btn.pack(side=tk.LEFT)
            self.check_btn.pack(side=tk.LEFT)
            self.ce_check_btn.pack(side=tk.LEFT)
            self.check_btn['text'] = '生成CE检查脚本'
            self.export_btn.pack(side=tk.LEFT)
        else:
            self.check_btn.pack_forget()
            self.import2_btn.pack_forget()
            self.import_ce_log_btn.pack_forget()
            self.ce_check_btn.pack_forget()
            self.export_btn.pack_forget()
            self.check_btn['text'] = '检查'
            self.import2_btn.pack(side=tk.LEFT)
            self.check_btn.pack(side=tk.LEFT)
            self.export_btn.pack(side=tk.LEFT)



root = tk.Tk()
root.geometry('1000x380+800+300')
root.title('电信CE配置检查 R2020.8.7.1')
# root.resizable(0,0)
myapp = App(master=root)
myapp.mainloop()