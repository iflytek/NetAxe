# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# # @Time    : 2019/9/26 16:48
# # @Author  : dingyifei
#
# # 脚本作用：将读取的excel从第二行转换为list[list]的格式，不同数据类型都转换为str
#
# # import xlrd
# from datetime import datetime
# # from xlrd import xldate_as_tuple
#
# from netboost import settings
# from utils.db.mongo_ops import MongoOps
#
# BASE_DIR = settings.BASE_DIR
#
# mongo_1 = MongoOps(db='tmp', coll='01table')
#
#
# def excel2list(file):
#     print('filepath',file)
#     # 将读取的excel从第二行转换为list[list]的格式，不同数据类型都转换为str
#     # 0:空，1:str,2:float,3:日期，4：bool，5：error
#     # 读取excel表的数据
#     # workbook = xlrd.open_workbook(file)
#     workbook = ''
#     print(workbook)
#     # 选取需要读取数据的那一页
#     sheet = workbook.sheet_by_index(0)
#     # 获得行数和列数
#     rows = sheet.nrows
#     cols = sheet.ncols
#     # 创建一个数组用来存储excel中的数据
#     data_list = []
#     for row_num in range(1, rows):
#         data = []
#         for col_num in range(0, cols):
#             celltype = sheet.cell(row_num, col_num).ctype
#             cell = sheet.cell_value(row_num, col_num)
#             if celltype == 2 and cell % 1 == 0.0:  # float
#                 cell = str(int(cell))
#             elif celltype == 3:  # 日期
#                 # date = datetime(*xldate_as_tuple(cell, 0))
#                 date = ''
#                 cell = date.strftime('%Y-%m-%d')
#             elif celltype == 4:  # Bool
#                 cell = True if cell == 1 else False
#             elif celltype == 5:
#                 cell = 'error'
#             elif celltype == 0:
#                 cell = ""
#             else:
#                 cell = cell.strip()
#             data.append(cell)
#         data_list.append(data)
#     return data_list
#
#
#
#
#
#
#
#
#
# if __name__ == '__main__':
#
#     excel2list()
