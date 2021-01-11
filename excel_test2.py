import xlwings as xw
import os


def all_path(dirname):
    result = []
    for maindir, subdir, file_name_list in os.walk(dirname):
        # print("1:", maindir) #当前主目录
        # print("2:", subdir) #当前主目录下的所有目录
        # print("3:", file_name_list)  #当前主目录下的所有文件
        for filename in file_name_list:
            apath = os.path.join(maindir, filename)#合并成一个完整路径
            result.append(apath)
    return result


market_data_path = all_path('/Users/zy/Desktop/market_data')

for path in market_data_path:
    print(path)
    # 处理数据 读取excel，然后记录条数
    app = xw.App(visible=False, add_book=True)
    wb = app.books.open(path)
    sht = wb.sheets[0]
    print(sht.used_range.shape)


# sheet = wb.sheets.add('test')
# sheet.range('a1').value=[1,2,3]
# sheet.range('a2').value=[1, 'sdfsdfddf']
# # sheet.range('a1').value=123
# wb.save("excel//test2.xls")
# # wb.save('%s.xls' % time)  # 保存
# print(sheet.used_range.shape)
# wb.close()
# app.quit()


