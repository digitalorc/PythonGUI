from tkinter import *

int getNbit(unsigned int x, int n) { // getbit()
  return (x & (1 << n)) >> n;
};

def getbit(val, n) :
    return (val &(1<<n)) >> n)
val =     
# root = Tk()
# root.title("BiterrorCompare")
# root.geometry("800x1000")

# # listbox = Listbox(root, selectmode="extended", height=10)
# # listbox.insert(END,"사과")
# # listbox.insert(END,"딸기")
# # listbox.insert(END,"바나나")
# # listbox.insert(END,"수박")
# # listbox.insert(END,"포도")

# # listbox.pack()

# def btncmd():
# #     listbox.delete(END)
# #     print("List count is ", listbox.size())
#     pass
# # btn = Button(root, text="Click", command=btncmd)
# # btn.pack(side="left")

# # btn1 = Button(root, text="Click", command=btncmd)
# # btn1.pack(side="left")

btn_f16 = Button(root,text="F16")
btn_f17 = Button(root,text="F17")
btn_f18 = Button(root,text="F18")
btn_f19 = Button(root,text="F19")

btn_f16.grid(row=0, column=0)
btn_f17.grid(row=0, column=1)
btn_f18.grid(row=0, column=2)
btn_f19.grid(row=0, column=3)

btn_clear = Button(root, text="clear",width=10)
btn_equal = Button(root, text="=",width=10)
btn_div = Button(root, text="/",width=10)
btn_mul = Button(root, text="*",width=10)


btn_clear.grid(row=1, column=0)
btn_equal.grid(row=1, column=1)
btn_div.grid(row=1, column=2)
btn_mul.grid(row=1, column=3) 

# root.mainloop()

import tkinter
from math import *

window=tkinter.Tk()
window.title("YUN DAE HEE")
window.geometry("640x480+100+100")
window.resizable(False, False)

def calc(event):
    label.config(text="결과="+str(eval(entry.get())))

entry=tkinter.Entry(window)
entry.bind("<Return>", calc)
entry.pack()

label=tkinter.Label(window)
label.pack()

window.mainloop()