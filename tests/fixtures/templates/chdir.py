# -*- coding: utf-8 -*-

from troposphere import Template

from os import chdir


def sceptre_handler(sceptre_user_data):
    t = Template()

    chdir("..")

    return t.to_json()
