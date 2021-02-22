import builtins
from tkinter import *
import tkinter.font
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os, time, threading
from queue import Queue
from enum import Enum

#################################GLOVAL Variables ##########################################

masterFilePath = ""
dumpedFilePath = ""

pageAllowError = 0
pageSpareErrorAllowed = True
pageErrorIndex = 0

nandInfo = {
    'eraseBlockSize': 0,
    'pageSize': 0,
    'pageSpareSize': 0,
    'totalBlockCount': 0,
    'totalPageCount': 0
}

pageInfo = {
    'index': 0,
    'offset': 0,
    'dataBitErr': 0,
    'spareBitErr': 0
}

inspectionResult = {
    'totalErrorPage': 0,
    'totalDataBitError': 0,
    'totalSpareBitError': 0
}
pageList = []

q = Queue()
gPageIndex = 0


class threadState(Enum):
    Ready = 0
    Progress = 1
    Done = 2


_state = threadState.Ready


############################################################################################


#################################Global Functions ##########################################

def getbit(val, n):
    return (val & (1 << n)) >> n


def geterrorbitcount(value):
    err_count = 0
    for x in range(0, 8):
        if value & (1 << x):
            err_count += 1
    return err_count


## end of geterrorbitcount()

def inspection(data, q):
    global pageList, _state, gPageIndex

    totalPageCount = data[0]
    pageSize = data[1]
    spareSize = data[2]
    maxBitError = data[3]

    if len(masterFilePath) < 8 or len(dumpedFilePath) < 8:
        print("too low file size {}".format(len(masterFilePath)))
        _state = threadState.Done
        return
    try:
        masterF = open(masterFilePath, 'rb')
        dumpedF = open(dumpedFilePath, 'rb')
    except:
        messagebox.showerror("file error", "file is not valid!!")
        _state = threadState.Done
        return

    pageOffset = 0
    gPageIndex = 0
    _state = threadState.Progress
    for x in range(0, totalPageCount):
        if _state == threadState.Done:
            break;

        gPageIndex = x
        pageBytes1 = masterF.read(pageSize)
        pageSpareBytes1 = masterF.read(spareSize)
        pageBytes2 = dumpedF.read(pageSize)
        pageSpareBytes2 = dumpedF.read(spareSize)

        foundBitError = False
        pageInfo = {
            'index': 0,
            'offset': 0,
            'dataBitErr': 0,
            'spareBitErr': 0
        }

        for i in range(0, nandInfo['pageSize']):
            val = pageBytes1[i] ^ pageBytes2[i]
            if val != 0:
                bitErrCount = geterrorbitcount(val)
                if bitErrCount == 0:
                    print("val : " + str(val))
                pageInfo['dataBitErr'] += bitErrCount
                inspectionResult['totalDataBitError'] += pageInfo['dataBitErr']
                foundBitError = True

        if _state == threadState.Done:
            break;

        for i in range(0, nandInfo['pageSpareSize']):
            val = pageSpareBytes1[i] ^ pageSpareBytes2[i]
            if val != 0:
                bitErrCount = geterrorbitcount(val)
                if bitErrCount == 0:
                    print("val : " + str(val))
                pageInfo['spareBitErr'] += bitErrCount
                inspectionResult['totalSpareBitError'] += pageInfo['spareBitErr']
                foundBitError = True
        if foundBitError:
            if pageSpareErrorAllowed:
                if (pageInfo['dataBitErr'] + pageInfo['spareBitErr']) > maxBitError:
                    pageInfo['index'] = gPageIndex
                    pageInfo['offset'] = pageOffset
                    pageList.append(pageInfo)
                    q.put(pageInfo)
                    # printBitError(pageInfo)
            else:
                if (pageInfo['dataBitErr'] > maxBitError) or (pageInfo['spareBitErr'] > 1):
                    pageInfo['index'] = gPageIndex
                    pageInfo['offset'] = pageOffset
                    pageList.append(pageInfo)
                    q.put(pageInfo)

            # printBitError(pageInfo)  				
            inspectionResult['totalErrorPage'] += 1

        if _state == threadState.Done:
            break;
        pageOffset = masterF.tell() - (pageSize + spareSize)

        time.sleep(0.0005)  # 5 ms
    ## end for loop of entire file

    masterF.close()
    dumpedF.close()

    _state = threadState.Done
    pageErrorIndex = 0;


## end of inspection()


def uiUpdate(q):
    while True:
        data = q.get()
        printBitError(data)
        q.task_done()
        if _state == threadState.Done:
            print("UI thread is done!!!!!!")
            break;


def startTimer():
    global progressValue
    timer = threading.Timer(1, startTimer)
    timer.start()
    if _state == threadState.Done:
        timer.cancel()
        printStatic()

    if _state != threadState.Done:
        progressValue.set(int((gPageIndex / nandInfo['totalPageCount']) * 100))
    else:
        progressValue.set(100)
    # print("(progressVaue , page index) : "+str(int((gPageIndex/nandInfo['totalPageCount'])*100))+","+str(gPageIndex))
    progressBar.update()


def printNandInfo():
    message = "total-blocks:{}, total-pages:{}"
    listStatic.insert(END, message.format(nandInfo['totalBlockCount'], nandInfo['totalPageCount']))


## end of printNandInfo()

def printStatic():
    message = "Done!! error page count: {}, data bit errors :{}, spare bit errors:{}"
    listStatic.insert(END, message.format(inspectionResult['totalErrorPage'], inspectionResult['totalDataBitError'],
                                          inspectionResult['totalSpareBitError']))


## end of printStatic()

def printBitError(page):
    global pageErrorIndex
    # strMessage = "[{:06d}] [{:08X}] bit error : data:{:04d}  spare:{:02d}"     
    # listbox.insert(END, strMessage.format(page['index'], page['offset'], page['dataBitErr'], page['spareBitErr']) )
    tupleItem = (hex(page['offset']), page['dataBitErr'], page['spareBitErr'])
    tvList.insert('', 'end', text=pageErrorIndex, values=tupleItem)
    pageErrorIndex += 1


##end of printBitError()

def cmd_btnOpenFile1():
    global masterFilePath
    global pageAllowError
    nandInfo['eraseBlockSize'] = int(spinBlockSize.get()) * 1024
    nandInfo['pageSize'] = int(spinPagekSize.get())
    nandInfo['pageSpareSize'] = int(spinPageSparekSize.get())
    pageAllowError = int(spinMaxBitErr.get())

    masterFilePath = filedialog.askopenfilename(initialdir="/", title="Select Master file")
    print("master file :" + masterFilePath)
    entryFilePath1.delete(0, END)

    if len(masterFilePath) > 0:
        fSize = os.path.getsize(masterFilePath)

    if (fSize < 128 * 1024 * 1024):
        print("invalid file size")
        messagebox.showerror("file error", "file is not valid!!")
        masterFilePath = ""
        entryFilePath1.insert(0, "")
        return;

    pageCountPerBlock = nandInfo['eraseBlockSize'] / nandInfo['pageSize']
    realBlockSize = nandInfo['eraseBlockSize'] + pageCountPerBlock * nandInfo['pageSpareSize']
    nandInfo['totalBlockCount'] = int(fSize / realBlockSize)
    nandInfo['totalPageCount'] = int(pageCountPerBlock * nandInfo['totalBlockCount'])

    printNandInfo()
    entryFilePath1.insert(0, masterFilePath)


##end of cmd_btnOpenFile1()


def cmd_btnOpenFile2():
    global dumpedFilePath
    global pageAllowError
    nandInfo['eraseBlockSize'] = int(spinBlockSize.get()) * 1024
    nandInfo['pageSize'] = int(spinPagekSize.get())
    nandInfo['pageSpareSize'] = int(spinPageSparekSize.get())
    pageAllowError = int(spinMaxBitErr.get())

    dumpedFilePath = filedialog.askopenfilename(initialdir="/", title="Select dump file")
    print("dump file :" + dumpedFilePath);
    entryFilePath2.delete(0, END)
    if len(dumpedFilePath) > 0:
        fSize = os.path.getsize(dumpedFilePath)
        if (fSize < 128 * 1024 * 1024):
            messagebox.showerror("file error", "file is not valid!!")
            dumpedFilePath = ""
            entryFilePath2.insert(0, "")
            return;

    pageCountPerBlock = nandInfo['eraseBlockSize'] / nandInfo['pageSize']
    realBlockSize = nandInfo['eraseBlockSize'] + pageCountPerBlock * nandInfo['pageSpareSize']
    nandInfo['totalBlockCount'] = int(fSize / realBlockSize)
    nandInfo['totalPageCount'] = int(pageCountPerBlock * nandInfo['totalBlockCount'])

    printNandInfo()
    entryFilePath2.insert(0, dumpedFilePath)


##end of cmd_btnOpenFile2()


def cleartvList():
    x = tvList.get_children()
    for item in x:
        tvList.delete(item)


def cmd_btnStartInpection():
    global _state

    if _state == threadState.Progress:
        return

    listStatic.delete(0, END)
    cleartvList()

    global pageAllowError
    nandInfo['eraseBlockSize'] = int(spinBlockSize.get()) * 1024
    nandInfo['pageSize'] = int(spinPagekSize.get())
    nandInfo['pageSpareSize'] = int(spinPageSparekSize.get())
    pageAllowError = int(spinMaxBitErr.get())

    params = (nandInfo['totalPageCount'], nandInfo['pageSize'], nandInfo['pageSpareSize'], pageAllowError)

    _state = threadState.Ready
    threadInspection = threading.Thread(target=inspection, args=(params, q))
    threadInspection.daemon = True;
    threadInspection.start()
    startTimer()

    threadUi = threading.Thread(target=uiUpdate, args=(q,))
    threadUi.daemon = True;
    threadUi.start()


## end of cmd_btnStartInpection()

############################################################################################


#################################GUI Initialization##########################################
root = Tk()
root.title("Bit Error Inspector")
root.geometry("800x1000")
root.resizable(width=False, height=True)

font = tkinter.font.Font(family='맑은 고딕', size=10, weight='bold')

frame1 = LabelFrame(root, text="Nand Parameters", height=300, relief='solid', bd=2, font=font)
frame1.pack(side=TOP, fill=X, padx=5, pady=5)

frame2 = LabelFrame(root, text="Master file", height=150, relief='solid', bd=2, font=font)
frame2.pack(side=TOP, fill=X, padx=5, pady=5)

frame3 = LabelFrame(root, text="Dump file", height=150, relief='solid', bd=2, font=font)
frame3.pack(side=TOP, fill=X, padx=5)

frame4 = LabelFrame(root, text="Inspection result", relief='solid', bd=2, font=font)
frame4.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=10)

# Nand Page paremeters ####################################################
label3 = Label(frame1, text="Block size (Kb)")
label3.grid(row=0, column=0)
defaultBlockSize = StringVar(root)
defaultBlockSize.set("128")
spinBlockSize = Spinbox(frame1, width=10, validate='none', from_=64, to=256, increment=64, state='readonly',
                        textvariable=defaultBlockSize)
spinBlockSize.grid(row=0, column=1, ipady=2, pady=5)

label4 = Label(frame1, text="Page size (Byte)")
label4.grid(row=1, column=0)
defaultPageSize = StringVar(root)
defaultPageSize.set("2048")
spinPagekSize = Spinbox(frame1, width=10, validate='none', from_=512, to=4096, increment=512, state='readonly',
                        textvariable=defaultPageSize)
spinPagekSize.grid(row=1, column=1, ipady=2, pady=5)

label5 = Label(frame1, text="Page Spare size (Byte)")
label5.grid(row=2, column=0)
defaultPageSpareSize = StringVar(root)
defaultPageSpareSize.set("128")
spinPageSparekSize = Spinbox(frame1, width=10, validate='none', from_=64, to=256, increment=64, state='readonly',
                             textvariable=defaultPageSpareSize)
spinPageSparekSize.grid(row=2, column=1, ipady=2, pady=5)

label6 = Label(frame1, text="Max Bit error (bit)")
label6.grid(row=3, column=0)
defaultMaxErr = StringVar(root)
defaultMaxErr.set("4")
spinMaxBitErr = Spinbox(frame1, width=10, validate='none', from_=0, to=8, textvariable=defaultMaxErr, state='readonly')
spinMaxBitErr.grid(row=3, column=1, ipady=2, pady=5)

listStatic = Listbox(frame1, selectmode="extended", height=10, font=('Calibri', 11))
listStatic.place(x=220, y=2, relwidth=0.7, relheight=0.9)
# #########################################################################

# File Open
entryFilePath1 = Entry(frame2)
entryFilePath1.pack(side=LEFT, padx=20, expand=True, fill=X)

btnOpenFile1 = Button(frame2, text="Open", command=cmd_btnOpenFile1, width=15)
btnOpenFile1.pack(side='right', padx=10, pady=10)

entryFilePath2 = Entry(frame3)
entryFilePath2.pack(side=LEFT, padx=20, expand=True, fill=X)

btnOpenFile2 = Button(frame3, text="Open", command=cmd_btnOpenFile2, width=15)
btnOpenFile2.pack(side='right', padx=10, pady=10)
###########################################################################


# result 
btnStart = Button(frame4, text="Start Inspection", command=cmd_btnStartInpection, height=3, width=20, fg='blue',
                  font=font)
btnStart.pack(side=RIGHT, padx=5, ipady=2)

listScroll = Scrollbar(frame4)
listScroll.pack(side=RIGHT, fill=Y)

progressValue = IntVar()
progressBar = ttk.Progressbar(frame4, maximum=100, mode='determinate', variable=progressValue)
progressBar.pack(side=BOTTOM, pady=2, padx=2, fill=X);

tvList = ttk.Treeview(frame4, columns=["1", "2", "3"], yscrollcommand=listScroll.set)
tvList.pack(side=BOTTOM, expand=True, padx=2, pady=5, fill=BOTH)
style = ttk.Style()
style.configure("Treeview.Heading", font=('Calibri', 11))

tvList.column("#0", width=100, anchor="w")
tvList.heading("#0", text="Num", anchor="center")

tvList.column("#1", width=120, anchor="w")
tvList.heading("1", text="page Offset", anchor="center")

tvList.column("#2", width=120, anchor="w")
tvList.heading("2", text="Data bit Error", anchor="center")

tvList.column("#3", width=120, anchor="w")
tvList.heading("3", text="Spare bit Error", anchor="center")

listScroll["command"] = tvList.yview

root.mainloop()
_state = threadState.Done
q.join()

# mainThread = threading.currentThread()
# for thread in threading.enumerate():
# # 	# Main Thread를 제외한 모든 Thread들이 
# # 	# 카운팅을 완료하고 끝날 때 까지 기다린다.
# 	if thread is not mainThread:
#  		thread.join()
