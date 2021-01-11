import datetime
import xlwings as xw


def create_xls():
    time = datetime.datetime.now().strftime("%Y-%m-%d ")
    wb = xw.Book()  # 创建新的工作簿
    sht = wb.sheets['Sheet1']  # 实例化工作表
    sht.range('A1').value = 'Hello World!'  # 写入
    print(sht.range('A1').value)  # 读取
    wb.save('%s.xls' % time)  # 保存
    wb.close()


# create_xls()

# wb = xw.Book('excel/0309.xls')
# Apps = xw.apps
# count = xw.apps.count
# keys = xw.apps.keys()
# print(Apps, count, keys)
# 创建工作簿
# app=xw.App()
# 是否可见、是否自动创建
app=xw.App(visible=True, add_book=False)
pid = app.pid
# 根据pid引用
app = xw.apps[1668]
# 返回当前活动App
app = xw.apps.active
# 激活app 当前桌面活跃窗口变为excel
app.activate(steal_focus=True)
# 退出App
# :通过杀掉进程强制Excel app退出
app.kill()
# :退出excel程序，不保存任何工作簿
app.quit()
# 重新计算一遍所有工作簿里的公式
app.calculate()
# 返回屏幕更新状态
print(app.screen_updating)
# '关闭屏幕更新   默认更新 True
# 关闭更新可以加速脚本运行，运行完毕之后，记住把screen_updating属性值改回 True
app.screen_updating = False
# App是否可见设置
# '返回App可见性
print(app.visible)
# '设置App为可见
app.visible = True
# 设置提醒信息是否显示 比如关闭前的保存提示、数据有效性的警告窗口，若想隐藏这些窗口，可进行如下设置
app.display_alerts=False
# 当前活动App的工作簿集合
books = xw.books
# '指定App的所有工作簿的集合
books = app.books

# 引用活动工作薄
wb = app.books.active
# 4. 激活
wb.activate()
# steal_focus=True, 则把窗口显示到最上层，并且把焦点从Python切换到Excel
wb.activate(steal_focus=True)
 # 保存
wb.save()
# 另存为 另存为时，可指定保存的位置、格式； 同名文件会在没有提示的情况下被覆盖
wb.save(r'D:\test.csv')
# 关闭 直接关闭工作簿，不会进行保存。
# 关闭所有的工作薄后，记得执行一遍 app.quit() 清理一下Excel程序
wb.close()
# --------------
# 获取工作簿的绝度路径
print(wb.fullname)
# 获取工作薄名称（带扩展名）
print(wb.name)
# 获取创建工作簿的App
print(wb.app)
# 返回工作薄中定义过的所有命名区域
print(wb.names)
# 更改计算模式  manual(手动) , automatic(自动) , semiautomatic(半自动)
wb.app.calculation = 'manual'
# Sheets:   工作簿包含的所有Sheet
# '当前活动工作薄
sheets = xw.sheets
# '指定工作薄 包括隐藏工作表及深度隐藏工作表
sheets2 = wb.sheets

# --------------------
# Sheet
# 新建 参数1为工作表名称，省略的话为Excel默认名称
# 参数2为插入位置，可选before或者after，示例中的代码表示插入到sheet2之后，省略的话插入到当前活动工作表之前
# 工作表名称重复的话会报错
sht = wb.sheets.add('test',after='sheet2')
# 引用
sht = wb.sheets('sheet1')
sht = wb.sheets(1)
# 当前活动工作表
sht = xw.sheets.active
# 激活
sht.activate()
# 清除
# 清除工作表所有内容和格式
# clear()不仅可以清除背景色等格式，还可以清除数据有效性和条件格式等
# “ 特别提醒：可以清除受保护的工作表的内容
sht.clear()
# 清除工作表的所有内容但是保留原有格式
sht.clear_contents()
# 删除 可以删除隐藏的工作表，但是不能删除深度隐藏的工作表
sht.delete()
# 自动调整行高列宽  行自适应 rows或r、列自适应 columns或c；
# 同时做行和列的自适应，不需要参数
sht.autofit('c')
# 选定工作表；只能在活动工作簿中选择
sht.select()

# ---------------
# 属性
# 1. 工作表名称
print(sht.name)
# '重命名工作表名称
sht.name = 'rename'
#2. 返回指定工作表所属的工作簿
print(sht.book)
# 3. 工作表上所有单元格的区域对象; 包括所有的单元格，不仅仅是那些正在使用中的单元格
print(sht.cells)
# 4. 返回工作表的索引值;按照Excel的方式，从1开始的
print(sht.index)
# 5. 返回所有与本工作表有关的命名区域
print(sht.names)
# 6. 工作表中用过的区域
print(sht.used_range)

# 打开代码所在路径下的文件
wb = app.books.open('test.xlsx')
wb = xw.Book('test.xlsx')

# 在当下app创建excel
wb = app.books.add()
# 创建一个新的App，并在新App中新建一个Book，报错，疑似当前app没有活跃窗口
# wb = xw.Book()
