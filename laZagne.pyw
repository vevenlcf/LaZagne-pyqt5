# -*- coding: utf-8 -*- 
# !/usr/bin/python

##############################################################################
#                                                                            #
#                           By Alessandro ZANNI                              #
#                                                                            #
##############################################################################

# Disclaimer: Do Not Use this program for illegal purposes ;)

import argparse
import logging
import sys
import time
import os

from lazagne.config.write_output import write_in_file, StandardOutput
from lazagne.config.manage_modules import get_categories
from lazagne.config.constant import constant
from lazagne.config.run import run_lazagne, create_module_dic

constant.st = StandardOutput()  # Object used to manage the output / write functions (cf write_output file)
modules = create_module_dic()


def output(output_dir=None, txt_format=False, json_format=False, all_format=False):
    if output_dir:
        if os.path.isdir(output_dir):
            constant.folder_name = output_dir
        else:
            print('[!] Specify a directory, not a file !')

    if txt_format:
        constant.output = 'txt'

    if json_format:
        constant.output = 'json'

    if all_format:
        constant.output = 'all'

    if constant.output:
        if not os.path.exists(constant.folder_name):
            os.makedirs(constant.folder_name)
            # constant.file_name_results = 'credentials' # let the choice of the name to the user

        if constant.output != 'json':
            constant.st.write_header()


def quiet_mode(is_quiet_mode=False):
    if is_quiet_mode:
        constant.quiet_mode = True


def verbosity(verbose=0):
    # Write on the console + debug file
    if verbose == 0:
        level = logging.CRITICAL
    elif verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    formatter = logging.Formatter(fmt='%(message)s')
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    # If other logging are set
    for r in root.handlers:
        r.setLevel(logging.CRITICAL)
    root.addHandler(stream)


def manage_advanced_options(user_password=None):
    if user_password:
        constant.user_password = user_password


def runLaZagne(category_selected='all', subcategories={}, password=None):
    """
    This function will be removed, still there for compatibility with other tools
    Everything is on the config/run.py file
    """
    for pwd_dic in run_lazagne(category_selected=category_selected, subcategories=subcategories, password=password):
        yield pwd_dic


def clean_args(arg):
    """
    Remove not necessary values to get only subcategories
    """
    for i in ['output', 'write_normal', 'write_json', 'write_all', 'verbose', 'auditType', 'quiet']:
        try:
            del arg[i]
        except Exception:
            pass
    return arg

from scan import *
from threading import Thread
from subprocess import run,Popen
from PyQt5.QtWidgets import (QFileDialog, QMainWindow, QApplication, QMessageBox, QSpinBox, QGridLayout)
from PyQt5 import QtGui
from PyQt5.QtCore import (QTimer, QCoreApplication, QThread, pyqtSignal)

class MyWindow(QMainWindow, Ui_MainWindow, QThread):

    # 定义了一个“message”信号，该信号接受str数据
    messageSignal = pyqtSignal(str)

    def __init__(self):
        super(MyWindow, self).__init__()
        self.setupUi(self)

        self.setWindowIcon(QtGui.QIcon('scan2.ico'))

        ###设置主题、图标
        self.setWindowTitle('主机密码扫描器v1.0 - By vevenlcf')

        ###信号处理：
        self.messageSignal.connect(self.showMessage)

        self.startButton.clicked.connect(self.buttonExec)
        self.endButton.clicked.connect(QCoreApplication.instance().quit)
        self.show()


    def showMessage(self,message):
        self.textEdit.append(message)

    def buttonExec(self):
        t = Thread(target=self.Work)
        # 在start前设置，可以保证在主线程终止时，子线程也终止
        # t.setDaemon(True)
        t.start()
        # 使用join方法会让主线程阻塞在这里，等待子线程结束，在里面可以设置阻塞的时间
        # t.join()


    def Work(self):
        self.pass_parse()

    def pass_parse(self):

        parser = argparse.ArgumentParser(description=constant.st.banner, formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('-version', action='version', version='Version ' + str(constant.CURRENT_VERSION),
                            help='laZagne version')

        # ------------------------------------------- Permanent options -------------------------------------------
        # Version and verbosity
        PPoptional = argparse.ArgumentParser(
            add_help=False,
            formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                max_help_position=constant.max_help)
        )
        PPoptional._optionals.title = 'optional arguments'
        PPoptional.add_argument('-v', dest='verbose', action='count', default=0, help='increase verbosity level')
        PPoptional.add_argument('-quiet', dest='quiet', action='store_true', default=False,
                                help='quiet mode: nothing is printed to the output')

        # Output
        PWrite = argparse.ArgumentParser(
            add_help=False,
            formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                max_help_position=constant.max_help)
        )
        PWrite._optionals.title = 'Output'
        PWrite.add_argument('-oN', dest='write_normal', action='store_true', default=None,
                            help='output file in a readable format')
        PWrite.add_argument('-oJ', dest='write_json', action='store_true', default=None,
                            help='output file in a json format')
        PWrite.add_argument('-oA', dest='write_all', action='store_true', default=None,
                            help='output file in both format')
        PWrite.add_argument('-output', dest='output', action='store', default='.',
                            help='destination path to store results (default:.)')

        # Windows user password
        PPwd = argparse.ArgumentParser(
            add_help=False,
            formatter_class=lambda prog: argparse.HelpFormatter(
                prog,
                max_help_position=constant.max_help)
        )
        PPwd._optionals.title = 'Windows User Password'
        PPwd.add_argument('-password', dest='password', action='store',
                          help='Windows user password (used to decrypt creds files)')

        # -------------------------- Add options and suboptions to all modules --------------------------
        all_subparser = []
        all_categories = get_categories()
        for c in all_categories:
            all_categories[c]['parser'] = argparse.ArgumentParser(
                add_help=False,
                formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                    max_help_position=constant.max_help)
            )
            all_categories[c]['parser']._optionals.title = all_categories[c]['help']

            # Manage options
            all_categories[c]['subparser'] = []
            for module in modules[c]:
                m = modules[c][module]
                all_categories[c]['parser'].add_argument(m.options['command'], action=m.options['action'],
                                                         dest=m.options['dest'], help=m.options['help'])

                # Manage all suboptions by modules
                if m.suboptions and m.name != 'thunderbird':
                    tmp = []
                    for sub in m.suboptions:
                        tmp_subparser = argparse.ArgumentParser(
                            add_help=False,
                            formatter_class=lambda prog: argparse.HelpFormatter(
                                prog,
                                max_help_position=constant.max_help)
                        )
                        tmp_subparser._optionals.title = sub['title']
                        if 'type' in sub:
                            tmp_subparser.add_argument(sub['command'], type=sub['type'], action=sub['action'],
                                                       dest=sub['dest'], help=sub['help'])
                        else:
                            tmp_subparser.add_argument(sub['command'], action=sub['action'], dest=sub['dest'],
                                                       help=sub['help'])
                        tmp.append(tmp_subparser)
                        all_subparser.append(tmp_subparser)
                        all_categories[c]['subparser'] += tmp

        # ------------------------------------------- Print all -------------------------------------------

        parents = [PPoptional] + all_subparser + [PPwd, PWrite]
        dic = {'all': {'parents': parents, 'help': 'Run all modules'}}
        for c in all_categories:
            parser_tab = [PPoptional, all_categories[c]['parser']]
            if 'subparser' in all_categories[c]:
                if all_categories[c]['subparser']:
                    parser_tab += all_categories[c]['subparser']
            parser_tab += [PPwd, PWrite]
            dic_tmp = {c: {'parents': parser_tab, 'help': 'Run %s module' % c}}
            # Concatenate 2 dic
            dic = dict(dic, **dic_tmp)

        # Main commands
        subparsers = parser.add_subparsers(help='Choose a main command')
        for d in dic:
            subparsers.add_parser(d, parents=dic[d]['parents'], help=dic[d]['help']).set_defaults(auditType=d)

        # ------------------------------------------- Parse arguments -------------------------------------------

        if len(sys.argv) == 1:
            sys.argv.insert(2, 'all')

        args = dict(parser.parse_args()._get_kwargs())
        arguments = parser.parse_args()

        quiet_mode(is_quiet_mode=args['quiet'])

        # Print the title
        constant.st.first_title()

        # Define constant variables
        output(
            output_dir=args['output'],
            txt_format=args['write_normal'],
            json_format=args['write_json'],
            all_format=args['write_all']
        )
        verbosity(verbose=args['verbose'])
        manage_advanced_options(user_password=args.get('password', None))

        start_time = time.time()

        category = args['auditType']
        subcategories = clean_args(args)

        for r in runLaZagne(category_selected=category, subcategories=subcategories,
                            password=args.get('password', None)):
            pass

        global res
        res = write_in_file(constant.stdout_result)
        print(res)

        tmp_str = str(res, encoding="UTF-8")
        for item in tmp_str.split('\r\n\r\n'):
            self.messageSignal.emit(item)

        constant.st.print_footer(elapsed_time=str(time.time() - start_time))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    myshow = MyWindow()
    sys.exit(app.exec_())