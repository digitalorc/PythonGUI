# import tkinter
# import tkinter.ttk

# window=tkinter.Tk()
# window.title("YUN DAE HEE")
# window.geometry("640x400+100+100")
# window.resizable(False, False)

# def cc(self):
#     treeview.tag_configure("tag2", background="red")

# treeview=tkinter.ttk.Treeview(window, columns=["1", "2", "3"])
# treeview.pack()

# treeview.column("#0", width=70)
# treeview.heading("#0", text="Num")

# treeview.column("#1", width=100, anchor="center")
# treeview.heading("1", text="Offset", anchor="center")

# treeview.column("#2", width=100, anchor="center")
# treeview.heading("2", text="Data Error", anchor="center")

# treeview.column("#3", width=100, anchor="center")
# treeview.heading("3", text="Data Error", anchor="center")

# treelist=[("A", "0x12345678",1) , ("B", "0x12345678",4), ("C", 0x12345678,0), ("D", 0x12345678,8), ("E", 0x1234DD8,1024)]

# for i in range(len(treelist)):    
#     treeview.insert('', 'end', text=i, values=treelist[i] )

# # top=treeview.insert('', 'end', text=str(len(treelist)), iid="5번", tags="tag1")
# # top_mid1=treeview.insert(top, 'end', text="5-2", values=["SOH", 1], iid="5번-1")
# # top_mid2=treeview.insert(top, 0, text="5-1", values=["NUL", 0], iid="5번-0", tags="tag2")
# # top_mid3=treeview.insert(top, 'end', text="5-3", values=["STX", 2], iid="5번-2", tags="tag2")

# # treeview.tag_bind("tag1", sequence="<<TreeviewSelect>>", callback=cc)

# window.mainloop()

import tkinter
import tkinter.ttk

window=tkinter.Tk()
window.title("YUN DAE HEE")
window.geometry("640x480+100+100")
# window.resizable(False, False)

button1=tkinter.LabelFrame(window, width=10, height=80, text="1번")
button1.pack(side='top', fill='x')

button2=tkinter.LabelFrame(window, width=10, height=50, text="2번")
button2.pack(side='top', fill='x')

# s=tkinter.ttk.Separator(window, orient="vertical")	
# s.pack(side='top', fill='x')

button3=tkinter.LabelFrame(window, width=10, height=50, text="3번")	
button3.pack(side='top', fill='x')
		
button4=tkinter.LabelFrame(window,  text="4번")
button4.pack(side='top',expand=True, fill='both')
		






window.mainloop()