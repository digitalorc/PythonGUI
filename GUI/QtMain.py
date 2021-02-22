import os
import time
from threading import Thread, Lock, Timer
from queue import Queue
from enum import Enum
from PyQt5 import uic
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox, QLineEdit,\
                            QCheckBox, QRadioButton,QProgressBar,QGroupBox,QFileDialog,QTableWidget,QSpinBox, \
                            QListWidget, QTableWidget, QTableWidgetItem,QHeaderView, QDialog, QLabel, \
                            QLineEdit
from PyQt5.QtCore import QTimer

form_class = uic.loadUiType("BITCompare.ui")[0]

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



class GUI(QDialog, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(645, 960)
        self._state = ThreadState.Ready

        self.tv_item_index = 0
        self.params = NandParam()
        
        self.total_error_pages = 0
        self.total_data_bit_errors = 0
        self.total_spare_bit_errors = 0

        self.bit_checker = BitChecker()
        self.q = self.bit_checker.get_message_queue()

        self.thread_ui = None
        self.progress_timer = QTimer()
        self.btn_open_master.clicked.connect(self.cmd_open_master_file)
        self.btn_open_dump.clicked.connect(self.cmd_open_dump_file)
        self.btn_start.clicked.connect(self.cmd_btn_start_inspection)
        self.progressbar.setValue(0)
        self.progress_timer.timeout.connect(self.timer_progress)
        self.msg = QMessageBox()

        headers = ['Page Offset', 'Data bit error', 'Spare bit error']
        self.table_result.setColumnCount(3)
        self.table_result.setHorizontalHeaderLabels(headers)
        # self.table_result.setSectionResizeMode(QHeaderView.Streth)
        self.show()

    def update_treeview_process(self,q):
        while self.bit_checker.get_thread_state() != ThreadState.Done:
            try:
                data = self.q.get(timeout=0.02)
                self.add_to_treeview(data)
                self.q.task_done()
            except:
                continue


    def timer_progress(self):
        current_pos = int((self.bit_checker.get_current_page_index() / self.params.total_pages) * 100)
        if self.bit_checker.get_thread_state() == ThreadState.Done:
                self.progress_timer.stop()
                result = self.bit_checker.get_inspection_result()
                self.total_error_pages = result[0]
                self.total_data_bit_errors = result[1]
                self.total_spare_bit_errors = result[2]
                self.print_inspection_log()
                self.btn_start.setText('Start')
        else:
            self.progressbar.setValue(current_pos)


    def print_file_log(self,title):
        message = title+'total-blocks:{}, total-pages:{}'
        self.label_result.clear()
        self.label_result.setText(message.format(self.params.total_blocks, self.params.total_pages))


    def print_inspection_log(self):
        message = 'Done!! error page count: {}, data bit errors :{}, spare bit errors:{}'
        self.label_result.clear()
        self.label_result.setText(message.format(self.total_error_pages, self.total_data_bit_errors,
                                              self.total_spare_bit_errors))


    def add_to_treeview(self, page):
        rows = self.table_result.rowCount()
        self.table_result.insertRow(rows)
        tv_item = (hex(page['offset']), str(page['dataBitErr']), str(page['spareBitErr']))
        for x in range(3):
            self.table_result.setItem(rows, x,QTableWidgetItem(tv_item[x]))

        print(self.tv_item_index )
        self.tv_item_index += 1


    def cmd_open_master_file(self):
        path = QFileDialog.getOpenFileName(caption='Open master file', directory='/')
        print(path[0])
        self.le_master_file_path.setText(path[0])

        if len(self.le_master_file_path.text()) > 0:
            file_len = os.path.getsize(self.le_master_file_path.text())
            if file_len < (128 * 1024 * 1024):
                print('invalid file size')
                self.show_error('file error','invalid file!!')
                self.le_master_file_path.clear()
                return


    def cmd_open_dump_file(self):
        if len(self.le_master_file_path.text()) < 10:
            self.show_error('file error','Open master file first!!')
            return
        path = QFileDialog.getOpenFileName(caption='Open dump file', directory='/')
        self.le_dump_file_path.setText(path[0])
        if len(self.le_dump_file_path.text()) > 0:
            file_len = os.path.getsize(self.le_dump_file_path.text())
            if file_len < (128 * 1024 * 1024):
                self.show_error('file error', 'file is not valid!!')
                self.le_dump_file_path.clear()
                return

    def show_error(self, title, msg, button_count=1):
        self.msg.setIcon(QMessageBox.Information)
        self.msg.setWindowTitle(title)
        self.msg.setText(msg)
        if button_count == 1:
            self.msg.setStandardButtons(QMessageBox.Ok )
        elif button_count == 2:
            self.msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = self.msg.exec_()

        return retval


    def clear_treeview(self):
        rows = self.table_result.rowCount()
        print(rows)
        for x in range(rows):
            self.table_result.removeRow(x)
        self.tv_item_index = 0
        self.progressbar.setValue(0)


    def cmd_btn_start_inspection(self):
        if self.bit_checker.get_thread_state() == ThreadState.Progress:
            self.progress_timer.stop()
            self.clear_treeview()
            self.bit_checker.stop()
            self.thread_ui.join()
            self.btn_start.setText('Start Inspection')
            return

        self.clear_treeview()

        if len(self.le_master_file_path.text()) > 0 and len(self.le_dump_file_path.text())>0:
            file_len = os.path.getsize(self.le_master_file_path.text())
            if file_len < (128 * 1024 * 1024):
                self.show_error('file error', 'file is not valid!!')
                self.le_master_file_path.clear()
                self.le_dump_file_path.clear()
                return

            erase_blk_size = page_len = page_spare_len = 0

            if self.radio_bl_128k.isChecked() == True:
                erase_blk_size = 128*1024
            if self.radio_bl_64k.isChecked() == True:
                erase_blk_size = 64*1024
            if self.radio_pg_2048b.isChecked() == True:
                page_len = 2048
            if self.radio_pg_512b.isChecked() == True:
                page_len = 512
            if self.radio_sp_128b.isChecked() == True:
                page_spare_len = 128
            if self.radio_sp_64b.isChecked() == True:
                page_spare_len = 64
            max_bit_error = self.spinbox_max_error.value()

            self.params.set(file_len,erase_blk_size, page_len, page_spare_len,max_bit_error, True)

            self.bit_checker.set_nand_param(self.le_master_file_path.text(), self.le_dump_file_path.text(),
                                            self.params.block_len, self.params.total_pages,
                                            self.params.page_len,  self.params.page_spare_len,
                                            self.params.max_bit_error,True)
            self.bit_checker.start()
            self.progressbar.setValue(0)
            self.progress_timer.start(1000)

            self.thread_ui = Thread(target=self.update_treeview_process, args=(self.q,))
            self.thread_ui.daemon = True
            self.thread_ui.start()

            self.btn_start.setText('Stop Inspection')

''' Bit error checking class'''


class BitChecker:

    def __init__(self):
        self.lock = Lock()

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
            with self.lock:
                self._state = ThreadState.Done
            return
        try:
            master_file_handle = open(self.master_file_path, 'rb')
            dump_file_handle = open(self.dump_file_path, 'rb')
        except:
            print('file error' + 'file is not valid!!')
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GUI()
    sys.exit(app.exec_())