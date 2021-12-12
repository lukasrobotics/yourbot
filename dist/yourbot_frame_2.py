import tkinter as tk
from tkinter import *
from tkinter import ttk
from functools import partial
import json, requests, urllib, io
from github import Github
from github import GithubException
import time
from tkinter.filedialog import askopenfilename, asksaveasfilename
import subprocess
import os 
import tkinter as tk
from tkinter import ttk
from tkinter import font
import keyword
import platform
from pygments import lex
from pygments.lexers import PythonLexer
import re



class TextLineNumbers(tk.Canvas):
    '''
        Canvas for Linenumbers
    '''
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None
        self.fontSize = 12
        self.configFont()
        self.config(bg='#362f2e')


    def configFont(self):
        system = platform.system().lower()
        if system == "windows":
            self.font = font.Font(family='monospace', size=self.fontSize)
        elif system == "linux":
            self.font = font.Font(family='monospace', size=self.fontSize)


    def attach(self, text_widget):
        self.textwidget = text_widget

    def redraw(self, *args):
        '''redraw line numbers'''
        self.delete("all")

        i = self.textwidget.index("@0,0")
        while True :
            dline= self.textwidget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(1,y,anchor="nw", font=self.font, text=linenum, fill='white')
            i = self.textwidget.index("%s+1line" % i)
        
        

class TextPad(tk.Text):
    '''
        modified text Widget ... thanks to stackoverflow.com :)
    '''
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        
        self.tk.eval('''
            proc widget_proxy {widget widget_command args} {

                # call the real tk widget command with the real args
                set result [uplevel [linsert $args 0 $widget_command]]

                # generate the event for certain types of commands
                if {([lindex $args 0] in {insert replace delete}) ||
                    ([lrange $args 0 2] == {mark set insert}) || 
                    ([lrange $args 0 1] == {xview moveto}) ||
                    ([lrange $args 0 1] == {xview scroll}) ||
                    ([lrange $args 0 1] == {yview moveto}) ||
                    ([lrange $args 0 1] == {yview scroll})} {

                    event generate  $widget <<Change>> -when tail
                }

                # return the result from the real widget command
                return $result
            }
            ''')
        self.tk.eval('''
            rename {widget} _{widget}
            interp alias {{}} ::{widget} {{}} widget_proxy {widget} _{widget}
        '''.format(widget=str(self)))
        
        self.filename = None
        self.tabWidth = 4
        self.clipboard = None
        self.entry = None
        
        self.fontSize = 13
        self.configFont()

        self.config(insertbackground='#00FF00')
        self.config(background='#362f2e')
        self.config(foreground='#FFFFFF')
        
        self.bind('<Return>', self.indent, add='+')
        self.bind('<Tab>', self.tab)
        self.bind('<BackSpace>', self.backtab)
        self.bind('<KeyRelease>', self.highlight, add='+')
        self.bind('<KeyRelease>', self.correctThisLine, add='+')
        #self.bind('<KeyPress-Return>', self.getDoublePoint)
        self.bind('<KeyRelease-Down>', self.correctLine)
        self.bind('<KeyRelease-Up>', self.correctLineUp)
        self.bind('<Key>', self.updateAutocompleteEntry, add='+')
        self.bind('<Control-x>', self.cut)
        self.bind('<Control-c>', self.copy)
        self.bind('<Control-v>', self.paste)
        #self.bind('<space>', self.highlight)
        
        self.autocompleteList = []
        self.SetAutoCompleteList()
        #print(self.autocompleteList)
        self.charstring = ''
        self.list = []
        
        # change selection color
        self.tag_config("sel", background="#47494c", foreground="white")
        

    
    def updateAutoCompleteList(self, event=None):
        '''
            a simple algorithm for parsing the given text and filter important words
        '''
        self.SetAutoCompleteList()
            
        autocompleteList = []
        liste = []
        text = self.get(1.0, tk.END)
        text = text.replace('"', " ").replace("'", " ").replace("(", " ").replace\
                        (")", " ").replace("[", " ").replace("]", " ").replace\
                        (':', " ").replace(',', " ").replace("<", " ").replace\
                        (">", " ").replace("/", " ").replace("=", " ").replace\
                        (";", " ").replace("self.", "").replace('.', ' ')
        
        liste = text.split('\n')
        
        for zeile in liste:
            if zeile.strip().startswith('#'):
                continue
            else:
                wortListe = zeile.split()
                for wort in wortListe:
                    if re.match("(^[0-9])", wort):
                        continue
                    elif '#' in wort or '//' in wort:
                        continue
                    elif wort in self.kwList:
                        continue
                    elif wort in self.autocompleteList:
                        continue
                    elif not len(wort) < 3:
                        w = re.sub("{}<>;,:]", '', wort)
                        #print(w)
                        autocompleteList.append(w)
        
        x = set(autocompleteList)
        autocompleteList = list(x)
        #print(autocompleteList)
        #self.autocompleteList = autocompleteList
        for word in autocompleteList:
            if len(word) > 30:
                continue
            self.autocompleteList.append(word)
        #print(self.autocompleteList)
        return
    
    
    def updateAutocompleteEntry(self, event=None):
        '''
            make new list for the input from the user
        '''
        char = event.char
        key = event.keycode
        sym = event.keysym
        
        # debugging ... :)
        #print(char)
        #print(key)
        
        self.list = []
        if (sym=='Space') or (sym=='Up') or (sym=='Down') or (sym=='Left') or (sym=='Right') \
            or (sym=='Shift_L') or (sym=='Shift_R') or (sym=='Control_R') or (sym=='Control_R') \
            or (sym=='Alt_L'):
                # set label and variables to none
                self.entry.config(text='---')
                self.list = []
                self.charstring = ''
        
        elif(char == '.') or (char == '(') or (char == ')') or (char=='"') or (char=="'") or \
            (char==',') or (char=='='):
                self.entry.config(text='---')
                self.list = []
                self.charstring = ''
        
        else:
            self.charstring += char
            
            for item in self.autocompleteList:
                if item.startswith(self.charstring):
                    self.list.append(item)
            
            if self.list:
                self.entry.config(text=self.list[0])                            
            else:
                self.entry.config(text='---')

            if len(self.list) == 3:
                self.entry.config(text=self.list[0])
                            
        
    def paste(self, event=None):
        '''
            paste method
        '''
        if self.clipboard == None:
            root = tk.Tk()                          # make tk instance
            root.withdraw()                         # don't display
            self.clipboard = root.clipboard_get()   # get clipboard
            root.clipboard_clear()                  # clear clipboard
            
        index = str(self.index(tk.INSERT))
        code = self.clipboard
        print(code)
        try:
            codelines = code.splitlines()
            for item in codelines:
                self.insert(tk.INSERT, item)
                self.insert(tk.INSERT, '\n')
                index = self.index('insert linestart')
                line = index.split('.')[0]
                line = int(line) - 1
                self.highlight(lineNumber=line)
                self.see(tk.INSERT)
        except:
            self.clipboard = None
            
        self.clipboard = None
        
        return 'break'
            
    
    def copy(self, event=None):
        '''
            copy method
        '''
        if self.tag_ranges("sel"):
            self.clipboard = self.get(tk.SEL_FIRST, tk.SEL_LAST)
            return 'break'

    
    def cut(self, event=None):
        '''
            cut method
        '''
        if self.tag_ranges("sel"):
            self.clipboard = self.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
            return 'break'


    def selectAll(self, event=None):
        self.tag_add('sel', '1.0', 'end')
    
    def indent(self, event=None):
        '''
            make indent
        '''
        self.entry.config(text='---')
        self.list = []
        self.charstring = ''

        self.highlight()
        index = self.index(tk.INSERT).split(".")
        line_no = int(index[0])
        pos = int(index[1])
        self.updateAutoCompleteList()
        if pos == 0:
            return
        line_text = self.get("%d.%d" % (line_no, 0),  "%d.end" % (line_no))
        text_only = line_text.lstrip(" ")
        no_of_spaces = len(line_text) - len(text_only)
        spaces = '\n' + " " * no_of_spaces
        if(no_of_spaces % 2 == 0):
            self.insert(tk.INSERT, spaces)

        else:
            while(no_of_spaces % 2 != 0): # is not
                no_of_spaces -= 1
                #print('spaces', no_of_spaces)
            spaces = '\n' + " " * no_of_spaces
            self.insert(tk.INSERT, spaces)

        #x, y = self.index(tk.INSERT).split('.')
        #x2, y2 = self.index('end-1c').split('.')
        #if x == x2:
        self.see(self.index(tk.INSERT)) 
        
        # on Return ends:
        self.correctLine()
        
        return 'break'
    
    def highlightThisLine(self, event=None):

        index = self.index('insert linestart')
        line = index.split('.')[0]
        
        line = int(line)
        
        
        if line > 0:
            self.highlight(lineNumber=line)

    
    def correctLine(self, event=None):
        index = self.index(tk.INSERT).split(".")
        line = int(index[0])
        line -= 1
        line_text = self.get("%d.%d" % (line, 0), "%d.end" % (line))
        self.delete("%d.0" % (line), "%d.end" %(line))
        self.insert("%d.0" % (line), line_text)
        
        if line > 0:
            self.highlight(lineNumber=line)

    def correctLineUp(self, event=None):
        index = self.index(tk.INSERT).split(".")
        line = int(index[0])
        line += 1
        line_text = self.get("%d.%d" % (line, 0), "%d.end" % (line))
        self.delete("%d.0" % (line), "%d.end" %(line))
        self.insert("%d.0" % (line), line_text)        
        
        if line > 0:
            self.highlight(lineNumber=line)
    
    def correctThisLine(self, event=None):
        ' to do   !!    -> event for <Key-Release>'
        key = event.keycode
        sym = event.keysym
        #print(key)
        #print(sym)
        # parenleft parenright () bracketleft bracketright [] braceleft braceright {}
        
        line = int(self.index(tk.INSERT).split('.')[0])
        line_text = self.get("%d.%d" % (line, 0), "%d.end" % (line))
        
        #for token, content in lex(line, PythonLexer()):


        if key == 51:   # -> #
            if line > 0:
                self.highlight(lineNumber=line)
        
        self.tag_configure("braceHighlight", foreground="red")
        self.tag_configure('parenHighlight', foreground='red')
        self.tag_configure('bracketHighlight', foreground='red')
                
        # paren ()
        if sym == 'parenleft':
            x = self.isBalancedParen(line_text)
            if x == False:
                z = line_text.rfind('(')
            else:
                z = False
            
            if z:
                self.tag_add("parenHighlight", "%d.%d"%(line, z), "%d.%d"%(line, z+1)) 
            else:
                self.tag_remove('parenHighlight', "%d.0"%(line), '%d.end'%(line))
        
        elif sym == 'parenright':
            x = self.isBalancedParen(line_text)
            if x == False:
                z = line_text.rfind(')')
            else:
                z = False
            
            if z:
                self.tag_add("parenHighlight", "%d.%d"%(line, z), "%d.%d"%(line, z+1)) 
            else:
                self.tag_remove('parenHighlight', "%d.0"%(line), '%d.end'%(line))
        
        # bracket []
        elif sym == 'bracketleft':
            x = self.isBalancedBracket(line_text)
            if x == False:
                z = line_text.rfind('[')
            else:
                z = False
            
            if z:
                self.tag_add("bracketHighlight", "%d.%d"%(line, z), "%d.%d"%(line, z+1)) 
            else:
                self.tag_remove('bracketHighlight', "%d.0"%(line), '%d.end'%(line))
        
        elif sym == 'bracketright':
            x = self.isBalancedBracket(line_text)
            if x == False:
                z = line_text.rfind(']')
            else:
                z = False
            
            if z:
                self.tag_add("bracketHighlight", "%d.%d"%(line, z), "%d.%d"%(line, z+1)) 
            else:
                self.tag_remove('bracketHighlight', "%d.0"%(line), '%d.end'%(line))
        
        # brace {}
        elif sym == 'braceleft':
            x = self.isBalancedBrace(line_text)
            if x == False:
                z = line_text.rfind('{')
            else:
                z = False
            
            if z:
                self.tag_add("braceHighlight", "%d.%d"%(line, z), "%d.%d"%(line, z+1)) 
            else:
                self.tag_remove('braceHighlight', "%d.0"%(line), '%d.end'%(line))
        
        elif sym == 'braceright':
            x = self.isBalancedBrace(line_text)
            if x == False:
                z = line_text.rfind('}')
            else:
                z = False
            
            if z:
                self.tag_add("braceHighlight", "%d.%d"%(line, z), "%d.%d"%(line, z+1)) 
            else:
                self.tag_remove('braceHighlight', "%d.0"%(line), '%d.end'%(line))


        else:
            return
        
    def isBalanced(self, txt):
        braced = 0
        for ch in txt:
            if (ch == '(') or (ch == '[') or (ch == '{'): 
                braced += 1
            if (ch == ')') or (ch == ']') or (ch == '}'):
                braced -= 1
                if braced < 0: return False
        return braced == 0


    def isBalancedParen(self, txt):
        braced = 0
        for ch in txt:
            if ch == '(': braced += 1
            if ch == ')':
                braced -= 1
                if braced < 0: return False
        return braced == 0

    def isBalancedBracket(self, txt):
        braced = 0
        for ch in txt:
            if ch == '[': braced += 1
            if ch == ']':
                braced -= 1
                if braced < 0: return False
        return braced == 0

    def isBalancedBrace(self, txt):
        braced = 0
        for ch in txt:
            if ch == '{': braced += 1
            if ch == '}':
                braced -= 1
                if braced < 0: return False
        return braced == 0

    
    def tab(self, event):
        '''
            make tab(4 * whitespaces) or insert autocomplete when using tab
        '''
        if not self.list:
            self.insert(tk.INSERT, " " * self.tabWidth)
        else:
            l = len(self.charstring)
            x, y = self.index(tk.INSERT).split(".")
            y2 = int(y) - l
            y2 = str(y2)
            pos = x + '.' + y2
            self.mark_set('insert', pos)
            self.tag_add("sel", pos, '%d.%d' % (int(x), int(y)))
            self.insert(tk.INSERT, self.list[0])
            if self.tag_ranges("sel"):      # test if selection...
                self.delete('sel.first', 'sel.last')
            self.charstring == ''
            self.entry.config(text='---')
            self.list = []
            self.highlight()

        return 'break'
    
    def backtab(self, event):
        '''
            make backtab when using backspace
        '''
        self.entry.config(text='---')
        self.list = []
        self.charstring = ''

        chars = self.get("insert linestart", 'insert')
        if not self.tag_ranges("sel"):
            if chars.isspace():     # only if there are whitespaces !
                if len(chars) >= 4:
                    self.delete("insert-4c", "insert")
                    return 'break'
        
        self.correctThisLine(event)
    
    def highlightOpen(self, text):
        index = self.index(tk.INSERT).split(".")
        line_no = int(index[0])
        
        lines = text.split('\n')
        i = 1
        
        for line in lines:
            self.insert('%d.0' % i, line)

            self.mark_set("range_start", '%d.0' %i)

            
            for token, content in lex(line, PythonLexer()):
                # Debug
                #print(token)

                self.tag_configure("Token.Name", foreground="#FFFFFF")
                self.tag_configure("Token.Text", foreground="#FFFFFF")

                self.tag_configure("Token.Keyword", foreground="#CC7A00")
                self.tag_configure("Token.Keyword.Constant", foreground="#CC7A00")
                self.tag_configure("Token.Keyword.Declaration", foreground="#CC7A00")
                self.tag_configure("Token.Keyword.Namespace", foreground="#CC7A00")
                self.tag_configure("Token.Keyword.Pseudo", foreground="#CC7A00")
                self.tag_configure("Token.Keyword.Reserved", foreground="#CC7A00")
                self.tag_configure("Token.Keyword.Type", foreground="#CC7A00")

                self.tag_configure("Token.Punctuation", foreground="#2d991d")

                self.tag_configure("Token.Name.Class", foreground="#ddd313")
                self.tag_configure("Token.Name.Exception", foreground="#ddd313")
                self.tag_configure("Token.Name.Function", foreground="#298fb5")
                self.tag_configure("Token.Name.Function.Magic", foreground="#298fb5")
                self.tag_configure("Token.Name.Decorator", foreground="#298fb5")

                        
                self.tag_configure("Token.Name.Builtin", foreground="#CC7A00")
                self.tag_configure("Token.Name.Builtin.Pseudo", foreground="#CC7A00")
                        

                self.tag_configure("Token.Operator.Word", foreground="#CC7A00")
                self.tag_configure("Token.Operator", foreground="#FF0000")

                self.tag_configure("Token.Comment", foreground="#767d87")
                self.tag_configure("Token.Comment.Single", foreground="#767d87")
                self.tag_configure("Token.Comment.Double", foreground="#767d87")

                self.tag_configure("Token.Literal.Number.Integer", foreground="#88daea")
                self.tag_configure("Token.Literal.Number.Float", foreground="#88daea")
            # 
                self.tag_configure("Token.Literal.String.Single", foreground="#35c666")
                self.tag_configure("Token.Literal.String.Double", foreground="#35c666")

            

                self.mark_set("range_end", "range_start + %dc" % len(content))
                self.tag_add(str(token), "range_start", "range_end")
                self.mark_set("range_start", "range_end")
                
            self.insert(tk.INSERT, '\n')
            i += 1
            self.update()

    
    def highlight(self, event=None, lineNumber=None):
        '''
            highlight the line where the cursor is ...
        '''
        
        index = self.index(tk.INSERT).split(".")
        line_no = int(index[0])
        if lineNumber == None:
            line_text = self.get("%d.%d" % (line_no, 0),  "%d.end" % (line_no))
            self.mark_set("range_start", str(line_no) + '.0')
        
        elif lineNumber is not None:
            line_text = self.get("%d.%d" % (lineNumber, 0), "%d.end" % (lineNumber))
            self.mark_set("range_start", str(lineNumber) + '.0')

        for token, content in lex(line_text, PythonLexer()):
            # Debug
            #print(token)
            self.tag_configure("Token.Name", foreground="#FFFFFF")
            self.tag_configure("Token.Text", foreground="#FFFFFF")

            self.tag_configure("Token.Keyword", foreground="#CC7A00")
            self.tag_configure("Token.Keyword.Constant", foreground="#CC7A00")
            self.tag_configure("Token.Keyword.Declaration", foreground="#CC7A00")
            self.tag_configure("Token.Keyword.Namespace", foreground="#CC7A00")
            self.tag_configure("Token.Keyword.Pseudo", foreground="#CC7A00")
            self.tag_configure("Token.Keyword.Reserved", foreground="#CC7A00")
            self.tag_configure("Token.Keyword.Type", foreground="#CC7A00")

            self.tag_configure("Token.Punctuation", foreground="#2d991d")

            self.tag_configure("Token.Name.Class", foreground="#ddd313")
            self.tag_configure("Token.Name.Exception", foreground="#ddd313")
            self.tag_configure("Token.Name.Function", foreground="#298fb5")
            self.tag_configure("Token.Name.Function.Magic", foreground="#298fb5")
            self.tag_configure("Token.Name.Decorator", foreground="#298fb5")

                        
            self.tag_configure("Token.Name.Builtin", foreground="#CC7A00")
            self.tag_configure("Token.Name.Builtin.Pseudo", foreground="#CC7A00")
                        

            self.tag_configure("Token.Operator.Word", foreground="#CC7A00")
            self.tag_configure("Token.Operator", foreground="#FF0000")

            self.tag_configure("Token.Comment", foreground="#767d87")
            self.tag_configure("Token.Comment.Single", foreground="#767d87")
            self.tag_configure("Token.Comment.Double", foreground="#767d87")

            self.tag_configure("Token.Literal.Number.Integer", foreground="#88daea")
            self.tag_configure("Token.Literal.Number.Float", foreground="#88daea")
            # 
            self.tag_configure("Token.Literal.String.Single", foreground="#35c666")
            self.tag_configure("Token.Literal.String.Double", foreground="#35c666")



            self.mark_set("range_end", "range_start + %dc" % len(content))
            self.tag_add(str(token), "range_start", "range_end")
            self.mark_set("range_start", "range_end")
    
    def highlightAll(self, event=None):
        '''
            highlight whole document (when loading a file) ... this can taking a few seconds
            if the file is big ..... no better solution found
        '''
        
        code = self.get("1.0", "end-1c")
        #print(code)
        i = 1
        for line in code.splitlines():
            self.index("%d.0" %i)
            self.highlight(lineNumber=i)
            self.update()
            i += 1

    def highlightAll2(self, linesInFile, overlord, event=None):
        '''
            highlight whole document (when loading a file) ... this can taking a few seconds
            if the file is big ..... no better solution found
        '''
        
        code = self.get("1.0", "end-1c")
        #print(code)
        i = 1
        for line in code.splitlines():
            self.index("%d.0" %i)
            self.highlight(lineNumber=i)
            percent = i/linesInFile*100
            percent = round(percent,2)
            overlord.title('Loading ... ' + str(percent) + ' %')
            i += 1


    
    def highlightAllOpen(self, code):
        pass

    def configFont(self):
        '''
            set the font .... tested only in windows .. if you want to make it cross platform
        '''
        system = platform.system().lower()
        if system == "windows":
            self.font = font.Font(family='Consolas', size=self.fontSize)
            self.configure(font=self.font)
        elif system == "linux":
            self.font = font.Font(family='Mono', size=self.fontSize)
            self.configure(font=self.font)

    def SetAutoCompleteList(self):
        '''
            basic autocompleteList with keywords and some important things (for me)
        '''
        self.autocompleteList = ['__init__', '__main__','__name__', '__repr__', '__str__',
                '__dict__', 'args', 'kwargs', "self", "__file__", 'super()'] # autocomplete

        self.kwList = keyword.kwlist
        for item in self.kwList:
            self.autocompleteList.append(item)


class Example(ttk.Frame):
    '''
        The Example App 
    '''

    def __init__(self, master=None):
        super().__init__(master)
        self.pack(expand=True, fill=tk.BOTH)
        self.initUI()
        self.style = ttk.Style()
        self.style.theme_use('clam')

    def initUI(self):
        
        #frame1
        frame1 = ttk.Frame(self)
        frame1.pack(fill=tk.BOTH, expand=True)
        
        # textPad
        self.textPad = TextPad(frame1, undo=True, maxundo=-1, autoseparators=True)
        self.textPad.filename = None
        self.textPad.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        textScrollY = ttk.Scrollbar(self.textPad)
        textScrollY.config(cursor="double_arrow")
        self.textPad.configure(yscrollcommand=textScrollY.set)
        textScrollY.config(command=self.textPad.yview)
        textScrollY.pack(side=tk.RIGHT, fill=tk.Y)

        # autocompleteEntry
        self.autocompleteEntry = tk.Label(self, fg='green', text='- - -', font=('Mono', 13))
        self.autocompleteEntry.pack(side='left', fill='y')
        self.textPad.entry = self.autocompleteEntry
        
        self.linenumber = TextLineNumbers(frame1, width=30)
        self.linenumber.attach(self.textPad)
        self.linenumber.pack(side="left", fill="y")
        
        
        self.textPad.bind("<<Change>>", self.on_change)
        self.textPad.bind("<Configure>", self.on_change)

    def on_change(self, event):
        self.linenumber.redraw()
        
        

root = tk.Tk()
global verified_pas
global user_taken 
global container
gpath = ''

my_profile_Name ='0' # bei loggin auf mein username setzen

actual_task = StringVar()
actual_task.set('')

task_list_update_list = StringVar()
task_list_update_list.set('')

actual_Profile = StringVar()
actual_Profile.set('')

actual_Profile_name = StringVar()
actual_Profile_name.set('')

profile_description = ('                                                               \n                                                               				 \n---------------------------------------------------------------\nProfile description                                \n---------------------------------------------------------------\ninsert your description here                                                                                                \n                                                               \n                                                               		\n                                                               \n---------------------------------------------------------------\nexperience                                             \n---------------------------------------------------------------\ninsert your experience                                           \n                 \n---------------------------------------------------------------\nlatest projects                                             \n---------------------------------------------------------------\n                                                               \n                                                                 ')
			                                                              
task_description = ('---------------------------------------------------------------\nTask description                                \n---------------------------------------------------------------\ninsert here what this task is about                                                                                                \n                                                               \n                                                               		\n                                                               \n---------------------------------------------------------------\nadditional libraries                                             \n---------------------------------------------------------------\ninsert here which libraries you are using                                          \n                 \n---------------------------------------------------------------\nadditional Hardware                                             \n---------------------------------------------------------------\ninsert here which Hardware you are using and the configuration you are using for moveit                                         \n    ')

git_token= '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'

# using an access token
g = Github("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")
# Github Enterprise with custom hostname
hostname = 'lukasrobotics'
repo = g.get_repo("lukasrobotics/logindata")

task_collection = g.get_repo("lukasrobotics/task_collection")
comment_space = 0
global actual_Task_name_open
actual_Task_name_open =0
my_username = 'ubuntu'
version= 0.1


likes = StringVar()
likes.set('')
dislikes = StringVar()
dislikes.set('')
not_working = StringVar()
not_working.set('')

def update_task_list():
    print('update task list')
    contents = task_collection.get_contents("")
    count=0
    list_tasks=[]
    for x in contents:
		
        #print(count)
        contents_eins = contents[count].name#.decode()
        list_tasks.insert( count , contents_eins )
        count = count + 1
    
    task_list_update_list.set(list_tasks)          
    #li = des.split("\n")
    #des = li   					# funkt so mit absatz
    #actual_task.set(des)
    
def update_my_task_list():
    print('update my task list')
    
    my_task_list = repo.get_file_contents( str(  my_username + '/user_task_list.txt'  ) )
    my_task_list_d = str(my_task_list.decoded_content.decode()).split(" \n")
    
    task_list_update_list.set(my_task_list_d)
    
def update_profile_description( profile_path ): # profile path steht fuer username
    print('update profile description')
    description = repo.get_contents( str( profile_path + '/description.txt' )) 
    des = ( str(description.decoded_content.decode() ))
    li = des.split("\n")
    des = li   		# funkt so mit absatz
    actual_Profile.set(des)
    actual_Profile_name.set(profile_path)



class Page(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
    def show(self):
        self.lift()
    def hides(self):
        self.lower()

class Page1(Page): # create task
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       Profile_name= 'stevie'
       Task_Name='put & place'
       
       
       #username label and text entry box
       task_name_rLabel = tk.Label(self, text="Task name")
       task_name_rLabel.pack(side="top", fill="x", expand=False)

       task_name_r = tk.StringVar()
       
       #username_r.pack(side="top", fill="x", expand=False)
       task_name_rEntry = tk.Entry(self, textvariable= task_name_r, bg='#362f2e', fg='#d2ded1')
       task_name_rEntry.pack(side="top", fill="none", expand=False)
       
       label = tk.Label(self, text="Task code", fg = "black", font = "Times 15" )

       codeEntry = tk.Text(self, bg='#362f2e', fg='#d2ded1')

       label1 = tk.Label(self, text="Task description", fg = "black", font = "Times 15" )

       descriptionEntry = tk.Text(self,bg='#362f2e', fg='#d2ded1')
       descriptionEntry.insert(END, task_description)
       
       
       
       
       
       
       def create_new_task(Profile_name, task_name_r): # 
          # hey hey
          code = codeEntry.get("1.0","end")
          description = descriptionEntry.get("1.0","end")
          #my_profile_Name = Profile_name
          Task_Name = task_name_r.get()
          #print('PN', Profile_name)
          #print('TN', Task_Name)
          #print('TC', code)
          #print('TD', description)
          #print('topics', repo.get_contents(""))
          
          # search after username,password file
          task_name_r = ( str(task_name_r.get()) + '.txt' ) # funkt
          name_taken = 0
  
          try:
             contents_r = task_collection.get_contents(Task_Name)
             #str_list_r = contents_r.decoded_content.decode()
             #verified_pas_r = str_list_r.splitlines()[0]
             print('try_ to create task')
             
		    
          except GithubException as e:
             #verified_pas = 0
             #print('reg')
             #print(e.status) # 404 is not found funkt
             #print('Taskname already taken, please change your taskname')
             name_taken = e.status
		

          if  name_taken == 404:
             print('accepted, begin to create the task')	
             # go to next page

             #for contents auf namen test falls schon vergeben else pop up window and tell
             # task_collection files
             task_collection.create_file(str( Task_Name + '/creator.txt'), "init commit", my_username) # funkt und wenn nich schon existent kann gespeichert werden
             task_collection.create_file(str( Task_Name + '/' + Task_Name + '.py' ), "init commit", code)
             task_collection.create_file(str( Task_Name + '/description.txt'), "init commit", description)
             task_collection.create_file(str( Task_Name + '/comments_profile.txt'), "init commit", "")
             task_collection.create_file(str( Task_Name + '/comments_Text.txt'), "init commit", "")
             task_collection.create_file(str( Task_Name + '/like.txt'), "init commit", "")                  # safe profile names here in these
             task_collection.create_file(str( Task_Name + '/dislike.txt'), "init commit", "")
             task_collection.create_file(str( Task_Name + '/not_working.txt'), "init commit", "")
             
             # logindata and 
             # save additional to my_task list
             #repo.create_file( str( my_profile_Name + '/user_task_list.txt'  ) , "init commit", "" ) # hier fehl am platz hier update my project datei
             
             #print('my_profile_Name', my_username)
             #dislike_list = task_collection.get_file_contents( str(actual_Task_name_open + '/dislike.txt') )
             my_tasks_list = repo.get_file_contents( str(my_username + '/user_task_list.txt'))
             my_tasks_list_d = str(my_tasks_list.decoded_content.decode()).split("\n")
             
             
             
             my_tasks_list_d = str(my_tasks_list.decoded_content.decode() + Task_Name +" \n")

             # update
             repo.update_file(str(  my_username + '/user_task_list.txt'  ), "your_commit_message", my_tasks_list_d, my_tasks_list.sha)
             update_task_list()
             print('Task created')	
             p2.show()
             
             
             
          else:
             print('Taskname already taken, please change your taskname')
             
          return
          
          
          
          
          
          #for contents auf namen test falls schon vergeben else pop up window and tell
          #task_collection.create_file(str( Task_Name + '/creator.txt'), "init commit", my_profile_Name) # funkt und wenn nich schon existent kann gespeichert werden
          #task_collection.create_file(str( Task_Name + '/code.py'), "init commit", code)
          #update_task_list()
          #lambda : 
          

       
       
       create_new_task_init = partial(create_new_task, Profile_name, task_name_r,)
       
       
       button2 = tk.Button(self, text ="create new task & back", command = create_new_task_init ) 

       
       
       label.pack(side="top", fill="x", expand=False)
       button2.pack(side="top", fill="none", expand=False)
       codeEntry.pack(side = "top", fill = "both", expand = True)
       label1.pack(side="top", fill="x", expand=False)
       descriptionEntry.pack(side = "top", fill = "both", expand = True)
       

       # code , textfeld
       # description, textfeld
       # 




class Page2(Page):	#task
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       label = tk.Label(self, text="Tasks")
       label.pack(side="top", fill="x", expand=False)
       list_tasks = []
       count =0
       #repo = g.get_repo("PyGithub/PyGithub")
       contents = task_collection.get_contents("")
       for x in contents:
		
              #print(count)
              contents_eins = contents[count].name#.decode()
              list_tasks.insert( count , contents_eins )
              count=count+1
       task_list_update_list.set(list_tasks) 
       #print(list_tasks)
       #print(len(contents))
       #print(contents)
       #contents = contents[0].name#.decode()
       #for content_file in contents:
              #print(type(contents))
              #print(content_file)
              #print(type(content_file))
		
       #langs = ('Java', 'C#', 'C', 'C++', 'Python',
       #	'Go', 'JavaScript', 'PHP', 'Swift')
       
       #def search_tasks(search_t):
       #   print('search', search_t.get())
                    
       # serch block
       
       #username label and text entry box
       #search_t = tk.StringVar()
       #usernameEntry = tk.Entry(self, textvariable= search_t)
       #task_searching = partial(search_tasks, search_t)  
       #label = tk.Button(self, text="Search", command=task_searching)
       #label.pack( side="top", fill="none", expand=False, anchor='nw')
       #usernameEntry.pack(side="top", fill="none", expand=False, anchor= 'nw')
       #username_r = tk.StringVar()
       
       
       #list_tasks= ('Java', 'C#', 'C', 'C++', 'Python', 'Go', 'JavaScript', 'PHP', )
       #langs = list_tasks                  # here get einzelne names
       #count_list =0
       #for x in langs:
       #   e = str( x ) # + '                            +  ' +  '   -  ' + '     x  ')
       #   langs[count_list] = e
       #   count_list = count_list + 1
       #   print( 'x', x )
          
          
       #langs_var = tk.StringVar(value=langs)
       langs_var = str(task_list_update_list)
       listbox = tk.Listbox(
       self,
       bg='#362f2e', fg='#d2ded1',
       listvariable=(langs_var ),
       #height=20,
       #width=40,
       #selectmode='extended'
       )
       listbox.pack(side="left", fill="both", expand=True)
       
       def items_selected(event):                             # select single 
          selected_indices = listbox.curselection()
          selected_langs = [listbox.get(i) for i in selected_indices]
          
          #print( 'selected_langs', selected_langs[0] ) # + str(selected_langs[0])
          # -------------- ab hier comments
          task_collection_folder_path = ("lukasrobotics/task_collection")
          task_collection_folder = g.get_repo( task_collection_folder_path  )
          path = "/description.txt"
          description = task_collection_folder.get_contents( "/"+ selected_langs[0] + path ) 
          # geht nur so weil repositori nicht auf ordner zugreifen kann
          global actual_Task_name_open
          actual_Task_name_open = str(selected_langs[0])
          #print('actual_Task_name_open', actual_Task_name_open)
          # get the description of the project
          # get comment profile list
          profile_list = task_collection_folder.get_contents( "/"+ selected_langs[0] +"/comments_profile.txt" )
          # get comment list
          comment_profile_list = task_collection_folder.get_contents( "/"+ selected_langs[0] +"/comments_Text.txt" )
          # get length
          #length = len(profile_list)
          # add them to the description by their number by loop
          profile_list_d = str(profile_list.decoded_content.decode()).split(" \n °*> ")
          comment_profile_list = str(comment_profile_list.decoded_content.decode()).split(" \n °*> ")
          #print('length', len(profile_list_d))
          #print('description',  description.decoded_content.decode())   # with comments
          des = (str(description.decoded_content.decode()) + '\n-----\ncomments:\n-----'  ) 
          if  len(profile_list_d) > 1:
             count_list = 0
             for x in profile_list_d:
                if x != "":
                   des = str( des + '\n---\nUser: ' + profile_list_d[count_list] + '\n---\n' + comment_profile_list[count_list] ) 
                   
                   count_list = count_list + 1
                   print('x', x)
             
          
          li = des.split("\n")
          des = li   					# funkt so mit absatz
          actual_task.set(des) # hier dann noch alles an commentaren einfuegen, erst beide listen, dann max anzahl und beide dann nach counter abarbeiten
          # ------------- ab hier likes
          likes_list = task_collection_folder.get_contents( "/"+ selected_langs[0] + '/like.txt' )
          # get comment list
          dislikes_list = task_collection_folder.get_contents( "/"+ selected_langs[0] + '/dislike.txt' )
          not_working_list = task_collection_folder.get_contents( "/"+ selected_langs[0] + '/not_working.txt' )
          likes_list_d = str(likes_list.decoded_content.decode()).split(" \n °*> ")
          dislikes_list_d = str(dislikes_list.decoded_content.decode()).split(" \n °*> ")
          not_working_list_d = str(not_working_list.decoded_content.decode()).split(" \n °*> ")
          
          #print('care about likes', len(likes_list_d))
          #print('care about likes', len(dislikes_list_d))
          #print('care about likes', len(not_working_list_d))
          lik = str(len(likes_list_d) -1)
          likes.set(lik)
          dislikes.set(len(dislikes_list_d) -1)
          not_working.set( str(len(not_working_list_d) -1))
          p3.show()
          print('go to that task', selected_langs[0])
          
       
       listbox.bind('<<ListboxSelect>>', items_selected)
       
       # link a scrollbar to a list
       scrollbar = ttk.Scrollbar(
       self,
       orient='vertical',
       #width=20,
       command=listbox.yview
       )

       listbox['yscrollcommand'] = scrollbar.set

       #scrollbar.grid(
       #column=1,
       #row=0,
       #sticky='ns')
       scrollbar.pack(side="left", fill="y")
       

class Page3(Page): # liste task deskription
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       
       label = tk.Label(self, text="Task description", fg = "red", font = "Times 20" )
       label.pack(side="top", fill="x", expand=False)
       
       
       
       buttonframe = tk.Frame(self)
       
       buttonframe.pack(side="top", fill="x", expand=False)
       
       contents ='0'
       likes_list_c = str(likes.get())

       
       def get_task_download():
          print('get the file')
          #contents = repo.get_contents("525")
          #print('print out script', contents.decoded_content.decode())
          #contents=contents.decoded_content.decode()
          saveMyFileAs()
          #code = str(contents)
          #exec(code)


       def saveMyFileAs():
          print('save the file')
          global gpath
          gpath = '524.py'
          Task_name = 'putput'
          if gpath =='':
             path = asksaveasfilename(filetypes=[('Python Files','*.py')])
          else:
             path = gpath    
          with open(path, 'w') as file:
             #code = textEditor.get('1.0', END)
             # Parent Directory path
             parent_dir = "/home/ubuntu/"
             directory = Task_name
  
             # Path
             path = os.path.join(parent_dir, directory)
             os.mkdir(path)                                # creates folder but only once with error message then
             # for download code from this file -> code braucht fuer spaeter den selben namen
  
             contents = repo.get_contents(Task_name)
             contents=contents.decoded_content.decode()
             code = str(contents)
             file.write(code)
             gpath = path
             
             #command = f'python3 {gpath}'
    
             #process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
             
       def likessss():
          #likes_list_c = likes.get()
          #print('likes_list_c = likes.get()',likes_list_c )
          like_list = task_collection.get_file_contents( str(actual_Task_name_open + '/like.txt') )
          like_list_d = str(like_list.decoded_content.decode()).split(" \n °*> ")
          #print('like_list_d', like_list_d)
          if my_username in like_list_d:
             print('can not be liked again')
          else:
             print('liked')
             like_list_d = str(like_list.decoded_content.decode() + my_username +" \n °*> ")

             # update
             task_collection.update_file(actual_Task_name_open + '/like.txt', "your_commit_message", like_list_d, like_list.sha)
          
          
       def dislikess():
          #print('dislike')
          dislike_list = task_collection.get_file_contents( str(actual_Task_name_open + '/dislike.txt') )
          dislike_list_d = str(dislike_list.decoded_content.decode()).split(" \n °*> ")
          #print('not_working_list_d', dislike_list_d)
          if my_username in dislike_list_d:
             print('can not be disliked again')
          else:
             print('disliked')
             dislike_list_d = str(dislike_list.decoded_content.decode() + my_username +" \n °*> ")

             # update
             task_collection.update_file(actual_Task_name_open + '/dislike.txt', "your_commit_message", dislike_list_d, dislike_list.sha)
          
       def not_working_f():
          #print('not working')
          not_working_list = task_collection.get_file_contents( str(actual_Task_name_open + '/not_working.txt') )
          not_working_list_d = str(not_working_list.decoded_content.decode()).split(" \n °*> ")
          #print('not_working_list_d', not_working_list_d)
          if my_username in not_working_list_d:
             print('can not be not_working again')
          else:
             print('not_working')
             not_working_list_d = str(not_working_list.decoded_content.decode() + my_username +" \n °*> ")

             # update
             task_collection.update_file(actual_Task_name_open + '/not_working.txt', "your_commit_message", not_working_list_d, not_working_list.sha)
       
       t1 = tk.Button(buttonframe, text=str("  +  "), command=likessss) # profilnamen in liste einfuegen
       label_l = tk.Listbox( buttonframe, listvariable = str(likes), height=1, width=2, bg = 'light grey', selectmode='extended')
       
       t2 = tk.Button(buttonframe, text=str("  -  "), command=dislikess)
       label_dl = tk.Listbox( buttonframe, listvariable = str(dislikes), height=1, width=2, bg = 'light grey', selectmode='extended')
       t3 = tk.Button(buttonframe, text=str("  x  "), command=not_working_f)
       label_nw = tk.Listbox( buttonframe, listvariable = str(not_working), height=1, width=2, bg = 'light grey', selectmode='extended')
       t4 = tk.Button(buttonframe, text="   Get    ", command=get_task_download)
       label_abstand1 = tk.Label(buttonframe, text="  ")
       label_abstand2 = tk.Label(buttonframe, text="  ")
       label_abstand3 = tk.Label(buttonframe, text="  ")
       label_abstand4 = tk.Label(buttonframe, text="  ")
       
       label_abstand1.pack(side="left", fill="none")
       label_l.pack(side="left", fill="none")
       t1.pack(side="left", fill="x")
       label_abstand2.pack(side="left", fill="none")
       label_dl.pack(side="left", fill="none")
       t2.pack(side="left", fill="x")
       label_abstand3.pack(side="left", fill="none")
       label_nw.pack(side="left", fill="none")
       t3.pack(side="left", fill="x")
       label_abstand4.pack(side="left", fill="none")
       t4.pack(side="left", fill="x")
       
       def get_user_of_current_task():
          #actual_Task_name_open
          current_profile_name = task_collection.get_contents( "/"+ actual_Task_name_open + '/creator.txt' )
          current_profile_name_d = str(current_profile_name.decoded_content.decode())
          #print( 'c_p_n', current_profile_name_d )
          update_profile_description( current_profile_name_d )
          p5.show()
       
       tprof = tk.Button(buttonframe, text=str("creator profile"), command=get_user_of_current_task) # profilnamen in liste einfuegen
       tprof.pack(side="right", fill="x")
       
       
       
       commentEntry = tk.Text(self, height=5, bg='#362f2e', fg='#d2ded1',)
       def save_comment():
          print('saving comment')
          comment = commentEntry.get("1.0","end")
          # get the length of the existing list
          # add your profilename to the list
          #comment_list.append(my_profile_Name)
          #lenght = len(comment_list)
          # save the text under the length number + 1
          #comment_task_space = g.get_repo(str('lukasrobotics/task_collection/' + Task_Name + '/comments' ))
          #comment_task_space.create_file( lenght , "init commit", comment)
          
          #print( 'path', str(actual_Task_name_open ) )
          comment_list = task_collection.get_file_contents( str(actual_Task_name_open + "/comments_Text.txt") )
          comment_list_d = str(comment_list.decoded_content.decode() + comment +' \n °*> ')
          
          
          comment_profile_list = task_collection.get_file_contents( str(actual_Task_name_open + '/comments_profile.txt'))
          comment_profile_list_d = str(comment_profile_list.decoded_content.decode() + my_username +' \n °*> ')

          # update
          task_collection.update_file(actual_Task_name_open + '/comments_Text.txt', "your_commit_message", comment_list_d, comment_list.sha)
          task_collection.update_file(actual_Task_name_open + '/comments_profile.txt', "your_commit_message", comment_profile_list_d, comment_profile_list.sha)
       
       
       tc1 = tk.Button(commentEntry, text="comment", command=save_comment) 
       # comments profil in einer liste abspeichern und kommentar mit dem passenden indices dazu als txt datei speichern -> somit geordnet
       
       
       
    
       

       #contents = repo.get_contents("heydu.txt")      # get for loop get the profiles, the numbers of them and displace them by the numbers -> add the strings to the description in the right order
       				 # with loop dann immer erst Profil \n dann das commentar commentare auch in liste und dann einfach gemeinsam abarbeiten und an description anfuegen
       #str_list = contents.decoded_content.decode()
       #str_list = tk.StringVar(value=str_list)
       
       
       str_list =  str(actual_task) #("description here" + "\nso" + "\nwhat" + "\nis that") #list_tasks
       
       #print('str_list', str_list)
       #str_list = tk.StringVar(value = str_list)

       listbox = tk.Listbox( 
       self,
       listvariable = str_list, #  langs_var,
       bg='#362f2e', fg='#d2ded1',
       selectmode='extended')

       # link a scrollbar to a list
       scrollbar = ttk.Scrollbar(
       self,
       orient='vertical',
       #width=20,
       command=listbox.yview)
       
       scrollbar_x = ttk.Scrollbar(
       self,
       orient='horizontal',
       command=listbox.xview)


       listbox['yscrollcommand'] = scrollbar.set
       listbox['xscrollcommand'] = scrollbar_x.set
       scrollbar.pack(side="right", fill="y",  expand=False, anchor= 'e')
       
       listbox.pack(side="top", fill="both", expand=True, anchor='w')
       commentEntry.pack(side="top", fill="both", expand=False, anchor='w')
       tc1.pack(side="bottom", fill="none", expand=False, anchor='se')
       scrollbar_x.pack(side="top", fill="x",expand=False, anchor='s')

       
       
       
class Page4(Page):	# profile text change
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       
       # textfeld
       # speichern button
       #
       profile_description = repo.get_contents( "/"+ my_username + '/description.txt' )
       profile_description_d = str( profile_description.decoded_content.decode() )
       label = tk.Label(self, text="Profile", fg = "red", font = "Times 20" )
       label.pack(side="top", fill="x", expand=False)
       
       label1 = tk.Listbox(self, listvariable=actual_Profile_name, bg='lightgrey', fg='black', font = "Times 15", height=1  )
       label1.pack(side="top", fill="none", expand=False, anchor='n')
       
       ProfileEntry = tk.Text(self, height=5,bg='#362f2e', fg='#d2ded1',)
       ProfileEntry.insert(END, profile_description_d)
       
       def save_and_exit():
          print('save & back')
          # update
          description = ProfileEntry.get("1.0","end")
          repo.update_file(my_username + '/description.txt', "your_commit_message", description, profile_description.sha)
          update_profile_description( my_username )
          p5.show()
       
       
       tp1 = tk.Button(ProfileEntry, text="save & back", command=save_and_exit)
       ProfileEntry.pack(side="top", fill="both", expand=True, anchor='w')
       tp1.pack(side="bottom", fill="none", expand=False, anchor='se')

       
       


class Page5(Page): # Profile
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       
       label = tk.Label(self, text="Profile", fg = "red", font = "Times 20" )
       label.pack(side="top", fill="x", expand=False)
       label1 = tk.Listbox(self, listvariable=actual_Profile_name, bg="lightgrey", fg = "black", font = "Times 15", height=1  )
       label1.pack(side="top", fill="none", expand=False, anchor='n')
       
       buttonframe = tk.Frame(self)
       buttonframe.pack(side="top", fill="x", expand=False)


       t1 = tk.Button(buttonframe, text="change profile" , command= lambda : p4.show())
       #t2 = tk.Label(buttonframe, text="   -   ")
       #t3 = tk.Label(buttonframe, text="   x    ")
       #t4 = tk.Button(buttonframe, text="   Get    ", command= 0)#                           lambda : p2.show())
       
       
       t1.pack(side="right", fill="x")
       #t2.pack(side="left", fill="x")
       #t3.pack(side="left", fill="x")
       #t4.pack(side="left", fill="x")
     
       #contents = repo.get_contents("heydu.txt")
       #str_list = contents.decoded_content.decode()
       #str_list = tk.StringVar(value=str_list)
       str_list = str(actual_Profile)

       listbox = tk.Listbox( 
       self,
       listvariable = str_list, #  langs_var,
       bg='#362f2e', fg='#d2ded1',
       selectmode='extended')

       # link a scrollbar to a list
       scrollbar = ttk.Scrollbar(
       self,
       orient='vertical',
       #width=20,
       command=listbox.yview)
       
       scrollbar_x = ttk.Scrollbar(
       self,
       orient='horizontal',
       command=listbox.xview)


       listbox['yscrollcommand'] = scrollbar.set
       listbox['xscrollcommand'] = scrollbar_x.set
       scrollbar.pack(side="right", fill="y",  expand=False, anchor= 'e')
       listbox.pack(side="top", fill="both", expand=True, anchor='w')

       scrollbar_x.pack(side="top", fill="x",expand=False, anchor='s')

def hiders():
   #print('hide the others')
   p6.show()
       
class Page6(Page): # IDE
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)

       #textEditor = Text(self)
       #textEditor.config(bg='#362f2e', fg='#d2ded1', insertbackground='white')

       output = Text(self, height=4)
       output.config(bg='#362f2e', fg='#1dd604')
       
       #textEditor.pack(side = "top", fill = "both", expand = True)
       
       
       app = Example(self)
       app.pack(side = "top", fill = "both", expand = True)
       output.pack(side = "top", fill = "both", expand = False)
       #def print1():
          #print('hey was stheht:', app.textPad.get('1.0', END))
          
       #pr = tk.Button(self, text="Profile", command=print1)
       #pr.pack(side = "top", fill = "both", expand = True)
       def runMyCode():
          global gpath
          if gpath == '':
             saveMsg = Toplevel()
             msg = Label(saveMsg, text="Please save the file first")
             msg.pack()
             return
          print('command')
          command = f'python3 {gpath}'
          #print('subprocess')
          
          #subprocess.call(['open', '-W', '-a', 'Terminal.app'])
          #appscript.app('Terminal').do_script('python3 yourbot_frame_2.py')
          #os.system("ls -l")
          #subprocess.call(['gnome-terminal', '-x', 'python yourbot_frame_2.py'])
          #os.system("gnome-terminal -e 'bash -c \"sudo apt-get update; exec bash\"'")  # funkt
          #os.system("gnome-terminal -e 'bash -c \"sudo apt-get update; exec bash\"'")  # funkt
          #print('hey')
          #process = subprocess.call('start /wait python yourbot_frame_2.py', shell=True)

          process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
          print('output')
          outputResult, error = process.communicate()
          output.insert('1.0',outputResult)
          output.insert('1.0',error)
     

       def openMyFile():
          path = askopenfilename(filetypes=[('Python Files','*.py')])
          with open(path, 'r') as file:
             code = file.read()
             #textEditor.delete('1.0', END)
             
             #textEditor.insert('1.0', code)
             app.textPad.delete('1.0', END)
             app.textPad.insert('1.0', code)
             global gpath
             gpath = path

       def saveMyFileAs():
          
          path = asksaveasfilename(filetypes=[('Python Files','*.py'), ('Launch Files', '*.launch')])
          if path != '':
             with open(path, 'w') as file:
                code =  app.textPad.get('1.0', END)
                file.write(code)
             
       def saveMyFile():
          global gpath
          #sss = '   hey   - - - '.strip()
          #print('sss', sss)
          if gpath =='':
             path = asksaveasfilename(filetypes=[('Python Files','*.py'), ('Launch Files', '*.launch')])
          else:
             path = gpath    
          with open(path, 'w') as file:
             code =  app.textPad.get('1.0', END)
             file.write(code)
       
       def get_my_profile_description():      
             update_profile_description( my_username )
             p5.show()
             
       def get_my_task_list():
             update_my_task_list()
             p2.show()
       
       def get_task_list():
             update_task_list()
             p2.show()
             
             
       def buildallMyCode():
          global gpath
          if gpath == '':
             saveMsg = Toplevel()
             msg = Label(saveMsg, text="Please save the file first")
             msg.pack()
             return
          print('command')
          #command = f'python3 {gpath}'
          
          code =  app.textPad.get('1.0', END)
          
          
           
          pkg_name = app.textPad.get("%d.%d" % (1, 0), "%d.end" % (1))       # enter the package name here:
          dependencies = app.textPad.get("%d.%d" % (2, 0), "%d.end" % (2))   # enter all the dependencies here:
          datei_art = app.textPad.get("%d.%d" % (3, 0), "%d.end" % (3))      # enter if its a node or a launch file:
          config_start = app.textPad.get("%d.%d" % (4, 0), "%d.end" % (4))   # enter your config folder and file:
          
          
          pkg_name = pkg_name.replace("enter the package name here:","")
          pkg_name =  'lulu'#pkg_name.strip()
          dependencies = dependencies.replace("enter all the dependencies here:","")
          dependencies = 'rospy'#dependencies.strip()
          datei_art = datei_art.replace("enter if its a node or a launch file:","")
          datei_art = 'py'#datei_art.strip()
          config_start = config_start.replace("enter your config folder and file:","")
          config_start = config_start.strip()
          
          da_ = os.path.exists(str('/home/ubuntu/ws_moveit/src/' + pkg_name )) # /src/mytest_build.py')) # ('C:\\Users\\lifei\\Desktop')
          
          #if da_ == True : # existiert
             # datei speichern und build und runn alles oder launch
             #os.system("gnome-terminal -e 'bash -c \"cd ~/ws_moveit; catkin build --jobs 2\"'")
          
             #os.system("gnome-terminal -e 'bash -c \"roscore\"'")
             #config_path = str('roslaunch' + config_start)
             #os.system("gnome-terminal -e 'bash -c \"config_path'")
          
          
          
          #if da_ == False :
          # erstmal package install ,dann datei speichern, dann build, dann runn alles
          
          create_cat = str( 'catkin_create_pkg ' + pkg_name + ' ' + dependencies )
          path1 = str('/home/ubuntu/ws_moveit/src/' + pkg_name + '.'+ datei_art)
          with open(path1, 'w') as file:
                code =  app.textPad.get('1.0', END)
                print('code', code)
                file.write(code)
           
           
           
          #catkin_install_python(PROGRAMS\n
          #src/mytest_build.py\n
          #DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}\n
          #)
          
          datei = str( pkg_name + '.' + datei_art )
          desti = '\nDESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}\n)'
          datei_1 = str('catkin_install_python(PROGRAMS\nsrc/'+ pkg_name + '.'+ datei_art + desti)
          
          path2 = str('/home/ubuntu/ws_moveit/src/file1.txt')
          with open(path2, 'w') as file:
                #code =  app.textPad.get('1.0', END)
                #print('code', code)
                file.write(datei_1)
                
          #rauskopieren, zusammenfuegen, wieder rein kopieren, und rest loeschen
          
          #'cp'  + pkg_name + '.'+ datei_art + ' ' + pkg_name + '/src'
          source = 'source ~/ws_moveit/devel/setup.bash;cd ~/ws_moveit/src;'
          touch = str(';touch ' + pkg_name + '.'+ datei_art + ';')
          copy_code = str('cp -r '  + pkg_name + '.'+ datei_art + ' ' + pkg_name + '/src' +';')
          copy_cmake = str('cd ~/ws_moveit/src/'+ pkg_name + ';' +          'cp -r '  + 'CMakeLists.txt' + ' ' + '/home/ubuntu/ws_moveit/src/' +';'     + 'cd ~/ws_moveit/src;'         +'rm ' + pkg_name + '.'+ datei_art + ';'+ 'cd ~/ws_moveit/src;'+ 'mv CMakeLists.txt file2.txt'+ 'cat file2.txt file1.txt > CMakeLists.txt;'+'cp -r '  + 'CMakeLists.txt' + ' ' + pkg_name+'/CMakeLists.txt')
          remove_f = str('rm file2.txt;'+ 'rm file1.txt;' +'cd ~/ws_moveit/src/' + pkg_name) #+ 'rm CMakeLists.txt;'+ + 'rm CMakeLists.txt;'
          build = str(';cd ~/ws_moveit;catkin build --jobs 2;roscore;')
          
          complet_str = str (source + create_cat + touch + copy_code+ copy_cmake + remove_f + build ) 
          
          
          
          #type ' + '/home/ws_moveit/src/doc.py' + ' > ' + pkg_name + '.' + datei_art + ';
          #os.system(f"gnome-terminal -e 'bash -c \"source ~/ws_moveit/devel/setup.bash;cd ~/ws_moveit/src;{create_cat};touch {pkg_name}.{datei_art};type {code} > {pkg_name}.{datei_art};cd ~/ws_moveit;catkin build --jobs 2;roscore\"'")
          os.system(f"gnome-terminal -e 'bash -c \"{complet_str}\"'")
          #os.system("gnome-terminal -e 'bash -c \"cd ~/ws_moveit/src;cat file2.txt file1.txt > CMakeLists.txt;roscore\"'")
          #os.system(f"gnome-terminal -e 'bash -c \"cd ~/ws_moveit/src/lulu;cp -r CMakeLists.txt /home/ubuntu/ws_moveit/src;roscore\"'")
          
          # search folder by pkg name  os.path.isfile(path) true or false
          # launch file or pkg, dann bei string vorsilbe abziehen
          
          # config_data = 
          # config data via roslaunch and pkg name + launchfilename.
          print('td', pkg_name)
          print('dp', dependencies) # funkt beides
          
          #pkg_name = ?   # erste reihe immer pkg name
          #dependencies = ? # zweite line allways dependencies
          #create_cat = str( 'catkin_install_pkg ' + pkg_name + ' ' + dependencies )
          #pkg_folder_path = str( '/home/ubuntu/ws_moveit/src' )
          # manipulate CMakeLists.txt file
          # then catkin_make
          # was wenn du schon bei der datei bist? dann wird trozdem von home abgefragt und dann gebaut
          # wenn folder vorhandenn dirket einfach nur catkin make
          #os.system("gnome-terminal -e 'bash -c \"create_cat\"'")  # funkt
          
          
          
          

          #process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
          print('output')
          #outputResult, error = process.communicate()
          #output.insert('1.0',outputResult)
          #output.insert('1.0',error)
       
       menuBar = tk.Menu(root)
       fileBar = Menu(menuBar, tearoff=0)
       fileBar.add_command(label='Open', command = openMyFile)
       fileBar.add_command(label='Save', command = saveMyFile)
       fileBar.add_command(label='SaveAs', command = saveMyFileAs)
       fileBar.add_command(label='Exit', command =  exit)
       menuBar.add_cascade(label='File', menu = fileBar)
       
       
          
       runBar = Menu(menuBar, tearoff=0)
       runBar.add_command(label='Run', command = runMyCode)
       menuBar.add_cascade(label='Run', menu = runBar)
       
       buildrunBar = Menu(menuBar, tearoff=0)
       buildrunBar.add_command(label='Build all', command = buildallMyCode)
       #buildrunBar.add_command(label='Build this', command = buildallMyCode)   # hier noch fuer single einfuegen
       menuBar.add_cascade(label='Build', menu = buildrunBar)
       
       menuBar.add_command(label='Operations', command =  0) 
       menuBar.add_command(label='Tasks', command =  get_task_list)   #About)  # button in menue leiste funkt
       menuBar.add_command(label='Create task', command =  p1.show) 
       menuBar.add_command(label='Profile', command =  get_my_profile_description) 
       menuBar.add_command(label='My tasks', command =  get_my_task_list) 
       menuBar.add_command(label='IDE', command = hiders) 
       menuBar.add_command(label='Properties', command =  0) 
       menuBar.add_command(label='Configurations', command =  0) 
       root.configure(menu=menuBar)
       
 
       
       

class MainView(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        
        global p1 # create task
        global p2 # Task list
        global p3 # Task description
        global p4 # profile text change
        global p5 # Profile
        global p6 # IDE
        
                  # was brauch ich noch: profile adjust, create Task 
                  
        buttonframe = tk.Frame(self)
        container = tk.Frame(self)
        buttonframe.pack(side="top", fill="x", expand=False)

        container.pack(side="top", fill="both", expand=True)
        
        p2 = Page2(self)
        p1 = Page1(self)

        p3 = Page3(self)
        p4 = Page4(self)
        p5 = Page5(self)
        p6 = Page6(self)
        
        p2.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p1.place(in_=container, x=0, y=0, relwidth=1, relheight=1)

        p3.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p4.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p5.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p6.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p2.show()


        b1 = tk.Button(buttonframe, text="Login", command=p1.show)
        b2 = tk.Button(buttonframe, text="Tasks list", command=p2.show)
        b3 = tk.Button(buttonframe, text="Task", command=p3.show)
        b4 = tk.Button(buttonframe, text="Profile settings", command=p4.show)
        b5 = tk.Button(buttonframe, text="Profile", command=p5.show)
        
        
        
        b6 = tk.Button(buttonframe, text="IDE", command=p6.show)

        #b1.pack(side="left", fill="x")
        #b2.pack(side="left", fill="x")
        #b3.pack(side="left", fill="x")
        #b4.pack(side="left", fill="x")
        #b5.pack(side="left", fill="x")
        #b6.pack(side="left", fill="x")        
        
        

        
        

def validateLogin(username, password):
  
  # search after username,password file
  #print("username entered :", username.get())
  user_path = ( str(username.get()) + '.txt') # funkt
		
  try:
     contents = repo.get_contents(user_path)
     str_list = contents.decoded_content.decode()
     verified_pas = str_list.splitlines()[0]
		    
  except GithubException as e:
     verified_pas = 0
     #print(e.status) # 404 is not found funkt
		
     #print("password entered :", password.get())
     #print("password verified :", verified_pas )
  if password.get() == verified_pas:
     #lambda : controller.show_frame(Page3)
     frame = controller.show_frame(Page3)
     #frame.tkraise()
     #tk.Tk.show_frame(StartPage)
     print('accept')
			

  else:
     print('password or username wrong')        
			
  return

def register_new_user (username_r, password_r, e_mail_r): 
		
  # search after username,password file
  user_path_r = ( str(username_r.get()) + '.txt' ) # funkt
  user_taken = 0
  
  try:
     contents_r = repo.get_contents(user_path_r)
     #str_list_r = contents_r.decoded_content.decode()
     #verified_pas_r = str_list_r.splitlines()[0]
     #print('try')
     #print('un', username_r.get())
     #print('em', e_mail_r.get())
		    
  except GithubException as e:
     #verified_pas = 0
     #print('reg')
     #print(e.status) # 404 is not found funkt
     user_taken = e.status
		

  if  user_taken == 404:
     print('accepted create new user account')	
     # go to next page
     filename_new = (  str(username_r.get()) + '/' + str(username_r.get()) + '.txt' )
     
     pas_new = ( str( password_r.get()) + '\n' )
     user_new = ( str( username_r.get()) + '\n' )
     e_mail_new = (str(e_mail_r.get()) + '\n' )
     
     
     # ordner erstellen in logindata -> mit usernamen
     # unterdateinen erstellen
     repo.create_file( filename_new, "init commit", (  pas_new + user_new + e_mail_new)	)
     repo.create_file( str( username_r.get() + '/description.txt'  ), "init commit", profile_description )
     repo.create_file( str( username_r.get() + '/user_task_list.txt'  ), "init commit", '' )
  return


if __name__ == "__main__":
    
    
    # if sperre inaktiv 
    # oder if 
    # oder es passiert nichts
    start_list = []
    start_repo = g.get_repo("lukasrobotics/program")
    start_list = start_repo.get_contents( '27.txt' ) 
    st = ( str(start_list.decoded_content.decode() ))
    st_lst = st.split("\n")
    #print('st_lst', st_lst)
    #st_lst[1] = '1'
    #print('st_lst', st_lst)
      
    if (st_lst[0] == '0') and (st_lst[1] == '0'):
        #print('ds', profile_description)
        #print('td', task_description)
    
    
        def logged_inn():
           main = MainView(root)
           main.pack(side="top", fill="both", expand=True)
           label.destroy()
           usernameLabel.destroy()
           usernameEntry.destroy()
           passwordLabel.destroy()
           passwordEntry.destroy()
           loginButton.destroy()
           loginButton1.destroy()
           loginButton2.destroy()
           loginButton3.destroy()
           button2.destroy()
           my_username = 'ubuntu'
       
        def create_new_account():
           #main = MainView(root)
           #main.pack(side="top", fill="both", expand=True)
           label.destroy()
           usernameLabel.destroy()
           usernameEntry.destroy()
           passwordLabel.destroy()
           passwordEntry.destroy()
           loginButton.destroy()
           loginButton1.destroy()
           loginButton2.destroy()
           loginButton3.destroy()
           button2.destroy()
       
       
           label3 = tk.Label(root, text="Create new account", fg = "green", font = "Calibri 20" )
           label3.pack(side="top", fill="x", expand=False)
       
           label4 = tk.Label(root, text="USER")
           label4.pack(side="top", fill="x", expand=False)
       
           #username label and text entry box
           usernameLabel1 = tk.Label(root, text="User Name")
           usernameLabel1.pack(side="top", fill="x", expand=False)
           username_r1 = tk.StringVar()
       
           #username_r.pack(side="top", fill="x", expand=False)
           usernameEntry1 = tk.Entry(root, textvariable=username_r1)
           usernameEntry1.pack(side="top", fill="none", expand=False)
       
           e_mailLabel1 = tk.Label(root, text="E-Mail")
           e_mailLabel1.pack(side="top", fill="x", expand=False)
           e_mail_r = tk.StringVar()
       
           #username_r.pack(side="top", fill="x", expand=False)
           e_mailEntry1 = tk.Entry(root, textvariable=e_mail_r)
           e_mailEntry1.pack(side="top", fill="none", expand=False)

           #password label and password entry box
           passwordLabel1 = tk.Label(root,text="Password")
           passwordLabel1.pack(side="top", fill="x", expand=False)
           password_r1 = tk.StringVar()
           passwordEntry1 = tk.Entry(root, textvariable=password_r1, show='°')
           passwordEntry1.pack(side="top", fill="none", expand=False)

           register_new_user_p = partial(register_new_user, username_r1, password_r1, e_mail_r) 

           spacerLabel1 = tk.Label(root,text="")
           spacerLabel1.pack(side="top", fill="x", expand=False)

           button21 = tk.Button(root, text ="Create new account",command = register_new_user_p)
           button21.pack(side="top", fill="none", expand=False)
       
           #def back():
           #    print('will back')
           #    create_new_account.destroy()
           #button_back = tk.Button(root, text ="back",command = back)
           #button_back.pack(side="top", fill="none", expand=False)
       
    
        label = tk.Label(root, text="Login", fg = "red", font = "Calibri 20" )
        label.pack(side="top", fill="x", expand=False)
       
       
        #username label and text entry box
        usernameLabel = tk.Label(root, text="User Name")
        usernameLabel.pack(side="top", fill="x", expand=False)
        username_r = tk.StringVar()
       
        #username_r.pack(side="top", fill="x", expand=False)
        usernameEntry = tk.Entry(root, textvariable= username_r)
        usernameEntry.pack(side="top", fill="none", expand=False)

        #password label and password entry box
        passwordLabel = tk.Label(root,text="Password")
        passwordLabel.pack(side="top", fill="x", expand=False)
        password_r = tk.StringVar()
       
        passwordEntry = tk.Entry(root, textvariable= password_r, show='°')
        passwordEntry.pack(side="top", fill="none", expand=False)

        #validateLogin_1 = partial(register_new_user, username_r, password_r) #email)

        #login button
        loginButton = tk.Button(root, text="Login", command= logged_inn) 
        loginButton.pack(side="top", fill="none", expand=False)
        loginButton1 = tk.Label(root, text="") 
        loginButton1.pack(side="top", fill="none", expand=False) 
        loginButton2 = tk.Label(root, text="") 
        loginButton2.pack(side="top", fill="none", expand=False) 
        loginButton3 = tk.Label(root, text="") 
        loginButton3.pack(side="top", fill="none", expand=False)   
    
        button2 = tk.Button(root, text ="Create new account", command =create_new_account)
        button2.pack(side="top", fill="none", expand=False)

    
    
        root.wm_geometry("1200x700")
        root.title('YourBot')
        root.mainloop()
        
        
        
    else:
    
        if (st_lst[0] != '0'):
                print('global database offline.Shutdown, savety issues!')    
    
        if (st_lst[1] != '0'):
                start_repo = g.get_repo("lukasrobotics/program")
                version_str = start_repo.get_contents( str('new_version' + st_lst[1] + '.txt') )
                version_str_d = ( str(version_str.decoded_content.decode() ))
                
                try:
                    root.destroy()
                    
                except:
                    print('')
                    
                exec(version_str_d)
                

    #root.mainloop()
    
    
    
    
#class Page4(Page):	# registration
#   def __init__(self, *args, **kwargs):
 #      Page.__init__(self, *args, **kwargs)
  #     
       #
#      
#       label = tk.Label(self, text="Create new account", fg = "green", font = "Calibri 20" )
#       label.pack(side="top", fill="x", expand=False)
#       
#       label = tk.Label(self, text="USER")
#       label.pack(side="top", fill="x", expand=False)
#       
#       #username label and text entry box
#       usernameLabel = tk.Label(self, text="User Name")
#       usernameLabel.pack(side="top", fill="x", expand=False)
#       username_r = tk.StringVar()
#       
#       #username_r.pack(side="top", fill="x", expand=False)
#       usernameEntry = tk.Entry(self, textvariable=username_r)
#       usernameEntry.pack(side="top", fill="none", expand=False)
#
#       #password label and password entry box
#       passwordLabel = tk.Label(self,text="Password")
#       passwordLabel.pack(side="top", fill="x", expand=False)
#       password_r = tk.StringVar()
#       passwordEntry = tk.Entry(self, textvariable=password_r, show='*')
#       passwordEntry.pack(side="top", fill="none", expand=False)

       #validateLogin_1 = partial(register_new_user, username_r, password_r) #email)
#
       #login button
#       loginButton = tk.Button(self, text="Login", command= 0)
#       loginButton.pack(side="top", fill="none", expand=False)  

#       button2 = tk.Button(self, text ="Create new account",command = 0)
#       button2.pack(side="top", fill="none", expand=False)



#class Page1(Page): # login
#   def __init__(self, *args, **kwargs):
#       Page.__init__(self, *args, **kwargs)
##
#
#       
#       label = tk.Label(self, text="Login", fg = "red", font = "Calibri 20" )
#       label.pack(side="top", fill="x", expand=False)
#       
#       label = tk.Label(self, text="USER")
#       label.pack(side="top", fill="x", expand=False)
#       
#       #username label and text entry box
#       usernameLabel = tk.Label(self, text="User Name")
#       usernameLabel.pack(side="top", fill="x", expand=False)
#       username_r = tk.StringVar()
#       
#       #username_r.pack(side="top", fill="x", expand=False)
#       usernameEntry = tk.Entry(self, textvariable= username_r)
#       usernameEntry.pack(side="top", fill="none", expand=False)#
#
#       #password label and password entry box
#       passwordLabel = tk.Label(self,text="Password")
#       passwordLabel.pack(side="top", fill="x", expand=False)
#       password_r = tk.StringVar()
#       
#       passwordEntry = tk.Entry(self, textvariable= password_r, show='°')
#       passwordEntry.pack(side="top", fill="none", expand=False)#

       #validateLogin_1 = partial(register_new_user, username_r, password_r) #email)

       #login button
#       loginButton = tk.Button(self, text="Login", command= 0) 
#       loginButton.pack(side="top", fill="none", expand=False)  
#
#       button2 = tk.Button(self, text ="Create new account", command =lambda: p2.show())# p3.show)
#       button2.pack(side="top", fill="none", expand=False)

    
