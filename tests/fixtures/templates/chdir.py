# -*- coding: utf-8 -*-

from troposphere import Template

from os import chdir, getcwd


def sceptre_handler(sceptre_user_data):
    t = Template()

    curr_dir = getcwd()
    chdir("..")
    chdir(curr_dir)

    return t.to_json()
