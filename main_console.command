#!/usr/bin/env /Users/rundaoli/opt/anaconda3/bin/python

from tools import *

env = DataSolver()

str_func = '1. 从文件录入比赛信息\n'
str_func += '2. 设置环境时间（用于改变导出成绩的计算日期）\n'
str_func += '3. 添加成员\n'
str_func += '4. 导出当前成绩\n'
str_func += '5. 导出成绩历史记录\n'
str_func += '6. 根据比赛记录重新生成数据库\n'
str_func += '0. 退出\n'

while True:
    print(str_func)
    try:
        choice = int(input('请输入您的选择：'))
    except ValueError:
        print('输入错误，请重新输入！')
        continue
    if choice == 1:
        env.add_match_file()
        continue
    elif choice == 2:
        env.set_t_comp_input()
        continue
    elif choice == 3:
        env.add_new_player()
        continue
    elif choice == 4:
        env.export_score()
    elif choice == 5:
        env.export_score_history()
    elif choice == 6:
        env.regenerate_from_match_log()
    elif choice == 0:
        print('感谢使用！')
    else:
        print('输入错误，请重新输入！')
        continue
    break
