import wx
from wattcherMore import update_graph


TRAY_TOOLTIP = 'Electrotecnia'
TRAY_ICON = 'icon.png'
runSystem = False

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.AppendItem(item)
    return item


class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self):
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Start', self.on_start)
        create_menu_item(menu, 'Stop', self.on_stop)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.IconFromBitmap(wx.Bitmap(path))
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):
        print 'Tray icon was left-clicked.'

    def on_start(self, event):
        runSystem = True
        while runSystem:
            update_graph()


    def on_stop(self, event):
        runSystem = False


    def on_exit(self, event):
        wx.CallAfter(self.Destroy)


def main():
    app = wx.PySimpleApp()
    TaskBarIcon()
    app.MainLoop()


if __name__ == '__main__':
    main()
