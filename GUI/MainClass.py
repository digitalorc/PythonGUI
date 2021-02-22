from tkinter import Tk, ttk, messagebox,filedialog, Spinbox, Button, Entry, LabelFrame, Listbox, Label, Scrollbar
import tkinter.font
import os
import time
from threading import Thread, Lock, Timer
from queue import Queue
from enum import Enum


class ThreadState(Enum):
    Ready = 0
    Progress = 1
    Done = 2



class NandParam:
    def __init__(self):
        self.block_len =0
        self.page_len =0
        self.page_spare_len=0

        self.max_bit_error =0
        self.total_blocks =0
        self.total_pages =0
        self.include_spare_error = True

    def set(self, file_len, block_len, page_len, page_spare_len, max_bit_errors, include_spare_error):
        self.block_len = block_len
        self.page_len = page_len
        self.page_spare_len = page_spare_len
        self.max_bit_error = max_bit_errors
        pages_per_block = block_len/page_len
        real_block_size = block_len + (pages_per_block * page_spare_len)
        self.total_blocks = int(file_len/real_block_size)
        self.total_pages = int(file_len/(page_spare_len+page_len))
        self.include_spare_error = include_spare_error



class GUI:
    def __init__(self):
      
        self._state = ThreadState.Ready

        self.label3 = None
        self.label4 = None
        self.label5 = None
        self.label6 = None
        self.block_size = None
        self.spinbox_block = None
        self.spinbox_page = None
        self.spinbox_spare = None
        self.spinbox_max_bit = None
        self.listbox_log = None
        self.btn_open_master_file = None
        self.btn_open_dump_file = None
        self.btn_start_inspection = None
        self.scrollbar = None
        self.progressbar = None
        self.treeview = None
        self.entry_master_file_path = None
        self.entry_dump_file_path = None

        self.master_file_path = ''
        self.dump_file_path = ''
        self.var_page_area_size = None
        self.var_spare_are_size = None
        self.var_max_bit_err = None
        self.var_progress_value = None
        self.tv_item_index = 0
        self.params = NandParam()
        
        self.total_error_pages = 0
        self.total_data_bit_errors = 0
        self.total_spare_bit_errors = 0

        self.bit_checker = BitChecker()
        self.q = self.bit_checker.get_message_queue()
        
        self.root = Tk()        
        self.root.title('Bit Error Inspector')
        self.root.geometry('800x1000')
        self.root.resizable(width=False, height=True)

        self.root.protocol('WM_DELETE_WINDOW', self.on_close_window)

        self.font = tkinter.font.Font(family='맑은 고딕', size=10, weight='bold')

        self.frame1 = LabelFrame(self.root, text='Nand Parameters', height=300, relief='solid', bd=2, font=self.font)
        self.frame1.pack(side='top', fill='x', padx=5, pady=5)

        self.frame2 = LabelFrame(self.root, text='Master file', height=150, relief='solid', bd=2, font=self.font)
        self.frame2.pack(side='top', fill='x', padx=5, pady=5)

        self.frame3 = LabelFrame(self.root, text='Dump file', height=150, relief='solid', bd=2, font=self.font)
        self.frame3.pack(side='top', fill='x', padx=5)

        self.frame4 = LabelFrame(self.root, text='Inspection result', relief='solid', bd=2, font=self.font)
        self.frame4.pack(side='top', fill='both', expand=True, padx=5, pady=10)

        self.init_ui_nand_param()
        self.init_ui_inspect()

        self.thread_ui = None
        self.progress_timer = None


    def on_close_window(self):
        self.bit_checker.stop()

        if self.bit_checker.get_thread_state() == ThreadState.Progress:
            self.thread_ui.join()
            self.progress_timer.cancel()

        self.root.destroy()


    # noinspection PyPep8Naming
    def init_ui_nand_param(self):
        self.label3 = Label(self.frame1, text='Block size (Kb)')
        self.label3.grid(row=0, column=0)
        self.block_size = tkinter.StringVar()
        self.block_size.set('128')
        self.spinbox_block = Spinbox(self.frame1, width=10, validate='none', from_=64, to=256, increment=64,
                                  state='readonly',
                                  textvariable=self.block_size)
        self.spinbox_block.grid(row=0, column=1, ipady=2, pady=5)

        self.label4 = Label(self.frame1, text='Page size (Byte)')
        self.label4.grid(row=1, column=0)
        self.var_page_area_size = tkinter.StringVar()
        self.var_page_area_size.set('2048')
        self.spinbox_page = Spinbox(self.frame1, width=10, validate='none', from_=512, to=4096, increment=512,
                                      state='readonly',
                                      textvariable=self.var_page_area_size)
        self.spinbox_page.grid(row=1, column=1, ipady=2, pady=5)

        self.label5 = Label(self.frame1, text='Page Spare size (Byte)')
        self.label5.grid(row=2, column=0)
        self.var_spare_are_size = tkinter.StringVar()
        self.var_spare_are_size.set('128')
        self.spinbox_spare = Spinbox(self.frame1, width=10, validate='none', from_=64, to=256, increment=64,
                                       state='readonly',
                                       textvariable=self.var_spare_are_size)
        self.spinbox_spare.grid(row=2, column=1, ipady=2, pady=5)

        self.label6 = Label(self.frame1, text='Max Bit error (bit)')
        self.label6.grid(row=3, column=0)
        self.var_max_bit_err = tkinter.StringVar()
        self.var_max_bit_err.set('4')
        self.spinbox_max_bit = Spinbox(self.frame1, width=10, validate='none', from_=0, to=8,
                                          textvariable=self.var_max_bit_err,
                                          state='readonly')
        self.spinbox_max_bit.grid(row=3, column=1, ipady=2, pady=5)

        self.listbox_log = Listbox(self.frame1, selectmode='extended', height=10, font = ('Calibri', 11))
        self.listbox_log.place(x=220, y=2, relwidth=0.7, relheight=0.9)


    def init_ui_inspect(self):
        # File Open , treeview
        self.entry_master_file_path = Entry(self.frame2)
        self.entry_master_file_path.pack(side='left', padx=20, expand=True, fill='x')

        self.btn_open_master_file = Button(self.frame2, text='Open', command=self.cmd_open_master_file, width=15)
        self.btn_open_master_file.pack(side='right', padx=10, pady=10)

        self.entry_dump_file_path = Entry(self.frame3)
        self.entry_dump_file_path.pack(side='left', padx=20, expand=True, fill='x')

        self.btn_open_dump_file = Button(self.frame3, text='Open', command=self.cmd_open_dump_file, width=15)
        self.btn_open_dump_file.pack(side='right', padx=10, pady=10)

        self.btn_start_inspection = Button(self.frame4, text='Start Inspection', command=self.cmd_btn_start_inspection,
                                           height=3, width=20,
                                           fg='blue',font=self.font)
        self.btn_start_inspection.pack(side='right', padx=5, ipady=2)

        self.scrollbar = Scrollbar(self.frame4)
        self.scrollbar.pack(side='right', fill='y')

        self.var_progress_value = tkinter.IntVar()
        self.progressbar = ttk.Progressbar(self.frame4, maximum=100, mode='determinate', variable=self.var_progress_value)
        self.progressbar.pack(side='bottom', pady=2, padx=2, fill='x');

        self.treeview = ttk.Treeview(self.frame4, columns=['1', '2', '3'], yscrollcommand=self.scrollbar.set)
        self.treeview.pack(side='bottom', expand=True, padx=2, pady=5, fill='both')
        style = ttk.Style()
        style.configure('Treeview.Heading', font=('Calibri', 11))

        self.treeview.column('#0', width=100, anchor='w')
        self.treeview.heading('#0', text='Num', anchor='center')

        self.treeview.column('#1', width=120, anchor='w')
        self.treeview.heading('1', text='page Offset', anchor='center')

        self.treeview.column('#2', width=120, anchor='w')
        self.treeview.heading('2', text='Data bit Error', anchor='center')

        self.treeview.column('#3', width=120, anchor='w')
        self.treeview.heading('3', text='Spare bit Error', anchor='center')
        self.scrollbar['command'] = self.treeview.yview


    def update_treeview_process(self,q):
        while self.bit_checker.get_thread_state() != ThreadState.Done:
            try:
                data = self.q.get(timeout=0.01)
                self.add_to_treeview(data)
                self.q.task_done()
            except:
                continue


    def start_timer_progress(self):
        self.progress_timer = Timer(1, self.start_timer_progress)
        self.progress_timer.start()
        current_pos = int((self.bit_checker.get_current_page_index() / self.params.total_pages) * 100)
        if self.bit_checker.get_thread_state() == ThreadState.Done:
            self.progress_timer.cancel()
            if current_pos >= 99:
                self.var_progress_value.set(100)
                self.progressbar.update()
                result = self.bit_checker.get_inspection_result()
                self.total_error_pages = result[0]
                self.total_data_bit_errors = result[1]
                self.total_spare_bit_errors = result[2]
                self.print_inspection_log()
                self.btn_start_inspection.configure(text='Start Inspection')
        else:
            self.var_progress_value.set(current_pos)
            self.progressbar.update()


    def print_file_log(self,title):
        message = title+'total-blocks:{}, total-pages:{}'
        self.listbox_log.insert('end', message.format(self.params.total_blocks, self.params.total_pages))


    def print_inspection_log(self):
        message = 'Done!! error page count: {}, data bit errors :{}, spare bit errors:{}'
        self.listbox_log.insert('end', message.format(self.total_error_pages, self.total_data_bit_errors,
                                              self.total_spare_bit_errors))


    def add_to_treeview(self, page):
        self.table_result.setItem( self.tv_item_index, )
        tv_item = (hex(page['offset']), page['dataBitErr'], page['spareBitErr'])
        self.treeview.insert('', 'end', text=self.tv_item_index, values=tv_item)
        self.tv_item_index += 1


    def cmd_open_master_file(self):
        self.master_file_path = filedialog.askopenfilename(initialdir='/', title='Select Master file')
        print('master file :' + self.master_file_path)
        self.entry_master_file_path.delete(0, 'end')

        if len(self.master_file_path) > 0:
            file_len = os.path.getsize(self.master_file_path)
            if file_len < (128 * 1024 * 1024):
                print('invalid file size')
                messagebox.showerror('file error', 'file is not valid!!')
                self.master_file_path = ''
                self.entry_master_file_path.delete(0,'end')
                return

            self.params.set(file_len,
                            int(self.spinbox_block.get()) * 1024,
                            int(self.spinbox_page.get()),
                            int(self.spinbox_spare.get()),
                            int(self.spinbox_max_bit.get()),
                            True)

            self.print_file_log('master file:')
            self.entry_master_file_path.insert(0, self.master_file_path)


    def cmd_open_dump_file(self):
        if len(self.master_file_path) < 10:
            messagebox.showerror('file error', 'Open master file first!!')
            return

        self.dump_file_path = filedialog.askopenfilename(initialdir='/', title='Select dump file')
        print('dump file :' + self.dump_file_path);
        self.entry_dump_file_path.delete(0, 'end')

        if len(self.dump_file_path) > 0:
            file_len = os.path.getsize(self.dump_file_path)
            if file_len < (128 * 1024 * 1024):
                messagebox.showerror('file error', 'file is not valid!!')
                self.dump_file_path = ''
                self.entry_dump_file_path.delete(0,'end')
                return

            self.print_file_log('dump file: ')
            self.entry_dump_file_path.insert(0, self.dump_file_path)


    def clear_treeview(self):
        x = self.treeview.get_children()
        for item in x:
            self.treeview.delete(item)
        self.tv_item_index = 0

        self.var_progress_value.set(0)
        self.progressbar.update()


    def cmd_btn_start_inspection(self):
        if self.bit_checker.get_thread_state() == ThreadState.Progress:
            self.clear_treeview()
            self.bit_checker.stop()
            self.thread_ui.join()
            self.progress_timer.cancel()
            self.btn_start_inspection.configure(text='Start Inspection')
            return

        self.listbox_log.delete(0, 'end')
        self.clear_treeview()

        if len(self.master_file_path) > 0 and len(self.dump_file_path)>0:
            file_len = os.path.getsize(self.master_file_path)
            if file_len < (128 * 1024 * 1024):
                print('invalid file size')
                messagebox.showerror('file error', 'file is not valid!!')
                self.master_file_path = ''
                self.entry_master_file_path.delete(0, 'end')
                return

            self.params.set(file_len,
                            int(self.spinbox_block.get()) * 1024,
                            int(self.spinbox_page.get()),
                            int(self.spinbox_spare.get()),
                            int(self.spinbox_max_bit.get()),
                            True)
            self.bit_checker.set_nand_param(self.master_file_path, self.dump_file_path,
                                            self.params.block_len, self.params.total_pages,
                                            self.params.page_len,  self.params.page_spare_len,
                                            self.params.max_bit_error,True)
            self.bit_checker.start()
            self.var_progress_value.set(0)
            self.progressbar.update()
            self.start_timer_progress()

            self.thread_ui = Thread(target=self.update_treeview_process, args=(self.q,))
            self.thread_ui.daemon = True
            self.thread_ui.start()

            self.btn_start_inspection.configure(text='Stop Inspection')

    def run(self):
        self.root.mainloop()

''' Bit error checking class'''


class BitChecker:

    def __init__(self):
        self.lock = Lock()
        self.master_file_path = ''
        self.dump_file_path = ''

        self.max_bit_error = 0
        self.spare_bit_error_okay = True
        self.thread_handle = 0

        self.erase_block_size = 0
        self.page_len = 0
        self.page_spare_len = 0
        self.current_page_index = 0
        self.error_page_list = []

        self.total_pages = 0
        self.total_error_pages = 0
        self.total_data_error_bits = 0
        self.total_spare_error_bits = 0

        self.q = Queue()
        self._state = ThreadState.Ready


    def start(self):
        self.thread_handle = Thread(target=self.inspection_process, args=(self.q,))
        self.thread_handle.daemon = True
        self.thread_handle.start()


    def stop(self):
        if self._state == ThreadState.Progress:
            with self.lock:
                self._state = ThreadState.Done
            self.thread_handle.join()
            self.q.join()


    def get_message_queue(self):
        return self.q


    def get_inspection_result(self):
        result = (self.total_error_pages,self.total_data_error_bits,self.total_spare_error_bits)
        return result


    def set_nand_param(self, master_f_path, dump_f_path, block_len, total_page_count, page_len, page_spare_len,
                       max_bit_error, spare_bit_error_okay):
        self.master_file_path = master_f_path
        self.dump_file_path = dump_f_path
        self.max_bit_error = int(max_bit_error)
        self.spare_bit_error_okay = spare_bit_error_okay
        self.erase_block_size = int(block_len)
        self.page_len = int(page_len)
        self.page_spare_len = int(page_spare_len)
        self.total_pages = int(total_page_count)


    def get_thread_state(self) -> ThreadState:
        return self._state


    def set_thread_state(self, state):
        with self.lock:
            self._state = state


    def get_current_page_index(self):
        return self.current_page_index


    def get_error_count(self, val):
        err_count = 0
        for x in range(0, 8):
            if val & (1 << x):
                err_count += 1
        return err_count


    def inspection_process(self, q):
        if len(self.master_file_path) < 8 or len(self.dump_file_path) < 8:
            print('too low file size {}'.format(len(self.master_file_path)))
            with self.lock:
                self._state = ThreadState.Done
            return
        try:
            master_file_handle = open(self.master_file_path, 'rb')
            dump_file_handle = open(self.dump_file_path, 'rb')
        except:
            messagebox.showerror('file error', 'file is not valid!!')
            with self.lock:
                self._state = ThreadState.Done
            return

        with self.lock:
            self._state = ThreadState.Progress

        page_offset = 0
        self.total_error_pages = 0
        self.error_page_list.clear()

        for x in range(0, self.total_pages):
            if self._state == ThreadState.Done:
                break
            self.current_page_index = x
            page_data1 = master_file_handle.read(self.page_len)
            page_spare_data1 = master_file_handle.read(self.page_spare_len)
            page_data2 = dump_file_handle.read(self.page_len)
            page_spare_data2 = dump_file_handle.read(self.page_spare_len)

            bit_error_found = False

            page_info = {
                'index': 0,
                'offset': 0,
                'dataBitErr': 0,
                'spareBitErr': 0
            }

            for i in range(self.page_len):
                val = page_data1[i] ^ page_data2[i]
                if val != 0:
                    bit_error_count = self.get_error_count(val)
                    if bit_error_count == 0:
                        print('val : ' + str(val))
                    page_info['dataBitErr'] += bit_error_count
                    self.total_data_error_bits += page_info['dataBitErr']
                    bit_error_found = True

            if self._state == ThreadState.Done:
                break

            for i in range(self.page_spare_len):
                val = page_spare_data1[i] ^ page_spare_data2[i]
                if val != 0:
                    bit_error_count = self.get_error_count(val)
                    if bit_error_count == 0:
                        print('val : ' + str(val))
                    page_info['spareBitErr'] += bit_error_count
                    self.total_spare_error_bits += page_info['spareBitErr']
                    bit_error_found = True

            if bit_error_found:
                if self.spare_bit_error_okay:
                    if (page_info['dataBitErr'] + page_info['spareBitErr']) > self.max_bit_error:
                        page_info['index'] = x
                        page_info['offset'] = page_offset
                        self.total_error_pages += 1
                        self.error_page_list.append(page_info)
                        self.q.put(page_info)
                        print("put ---page offset{} data error pages {}".format(hex(page_info['offset']) , page_info['dataBitErr']))
                else:
                    if (page_info['dataBitErr'] > self.max_bit_error) or (page_info['spareBitErr'] > 1):
                        page_info['index'] = x
                        page_info['offset'] = page_offset
                        self.total_error_pages += 1
                        self.error_page_list.append(page_info)
                        self.q.put(page_info)

            if self._state == ThreadState.Done:
                break

            page_offset = master_file_handle.tell() - (self.page_len + self.page_spare_len)

            time.sleep(0.0005)  # 5 ms
        ## end for loop of entire file

        master_file_handle.close()
        dump_file_handle.close()

        with self.lock:
            self._state = ThreadState.Done

# end of class


main = GUI()
main.run()
