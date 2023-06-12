import os
import winreg
import wx      
import subprocess
import sys
from PIL import Image


class MyFrame(wx.Frame):    
    def __init__(self):
        super(MyFrame,self).__init__(parent=None, title='Installazione quasi completata',size=(wx.DisplaySize()[0]*0.4, wx.DisplaySize()[1]*0.4),style= wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)
        panel = wx.Panel(self)        
        panel.SetBackgroundColour(wx.WHITE)
        my_sizer = wx.BoxSizer(wx.VERTICAL)
         
        ratio = 0.5
        # Carica l'immagine e comprimila alla risoluzione desiderata
        img = Image.open(os.path.dirname(os.path.realpath(__file__))+'\\Logo.png')
        
        window_size = self.GetSize()
        img_ratio = float(img.size[0]) / img.size[1]
        window_ratio = float(window_size[0]) / window_size[1]
        if img_ratio > window_ratio:
            img_size = (int(window_size[0]*ratio), int(window_size[0]*ratio/img_ratio))
        else:
            img_size = (int(window_size[1]*ratio*img_ratio), int(window_size[1]*ratio))
        img = img.resize(img_size, Image.ANTIALIAS)
        img.save('image_compressed.png', optimize=True, quality=95)

        # Aggiungi l'immagine compressa
        bmp = wx.Bitmap('image_compressed.png', wx.BITMAP_TYPE_ANY)
        my_bitmap = wx.StaticBitmap(panel, -1, bmp)
        my_sizer.Add(my_bitmap, 0, wx.ALL | wx.CENTER, 5)
        

        my_label = wx.StaticText(panel, label=u'Per finire l\'installazione \u00e8 necessario riavviare il PC')
        my_sizer.Add(my_label, 0, wx.ALL | wx.CENTER, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        my_btn = wx.Button(panel, label='Riavvia ora')
        button_sizer.Add(my_btn, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        my_btn.Bind(wx.EVT_BUTTON, self.on_press_now)

        my_btn1 = wx.Button(panel, label='Riavvia in seguito')
        button_sizer.Add(my_btn1, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        my_btn1.Bind(wx.EVT_BUTTON, self.on_press_later)

        my_sizer.Add(button_sizer, 0, wx.CENTER)
        panel.SetSizer(my_sizer)
        

        #set the size of window
        self.SetSize((bmp.GetWidth()+wx.DisplaySize()[0]*0.1,bmp.GetHeight()+100 ))
        #set the window in the center of screen
        self.Centre()

        self.Show()

    def on_press_now(self, event):
        print('Riavvio del PC in corso...')
        os.system('shutdown /r /t 0')

    def on_press_later(self, event):
        print('Riavvio del PC programmato per dopo.')
        exit(0)

if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame()




#installing arduino-cli
cmd = os.path.dirname(os.path.realpath(__file__))+"\\editor\\arduino\\bin\\arduino-cli-w32.exe config init --additional-urls \"https://dl.espressif.com/dl/package_esp32_index.json\""
os.system(cmd)
#updating index of arduino-cli
cmd = os.path.dirname(os.path.realpath(__file__))+"\\editor\\arduino\\bin\\arduino-cli-w32.exe core update-index"
os.system(cmd)
#installing esp32
cmd = os.path.dirname(os.path.realpath(__file__))+"\\editor\\arduino\\bin\\arduino-cli-w32.exe core install esp32:esp32"
os.system(cmd)
#installing driver
subprocess.call(['pnputil', '-i', '-a', os.path.dirname(os.path.realpath(__file__))+"\\DRIVER\\silabser.inf"])

#set environment variables

# Open the registry key for environment variables
key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0, winreg.KEY_ALL_ACCESS)

# Read the existing path value
actual_value = os.environ.get('Path')



var1 = "C:\\Python27"
var2 = "C:\\Python27\\Scripts"

var3 = os.path.dirname(os.path.realpath(__file__))+"\\lib\\GnuWin32\\bin"
var4 = os.path.dirname(os.path.realpath(__file__))+"\\lib\\MingW64\\bin"
var5 = os.path.dirname(os.path.realpath(__file__))+"\\editor\\arduino\\bin"

if actual_value.find(var1) != -1:
    var1 = ""
if actual_value.find(var2) != -1:
    var2 = ""
if actual_value.find(var3) != -1:
    var3 = ""
if actual_value.find(var4) != -1:
    var4 = ""
if actual_value.find(var5) != -1:
    var5 = ""

if var1 == "" and var2 == "" and var3 == "" and var4 == "" and var5 == "":
    print("Already in the environment variables")
else:
    print("Installing...")
    # Set the environment variable
    winreg.SetValueEx(key, 'Path', 0, winreg.REG_SZ, actual_value+";"+var1+";"+var2+";"+var3+";"+var4+";"+var5)

app.MainLoop()
