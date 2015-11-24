#!/usr/bin/env python3

import unittest

from configparser import ConfigParser
from datetime import datetime

from main import Browser_Controller
from main import Controller
from lib import demail

class TestMethods(unittest.TestCase):

    @unittest.skip("")
    def test_Browser_get_all_groups_data(self):
        b = Browser_Controller()
        team_info = b.get_all_groups_data()
        print(team_info)

    @unittest.skip("")
    def test_Browser_get_group_members(self):
        b = Browser_Controller()
        members = b.get_group_members("79d4b0d56cac41bd931fc772365772c4")
        print(members)

    def test_Controller_check_last_day_of_month(self):
        c = Controller()
        d = datetime(year=2015, month=2, day=28)
        rs = c.check_last_day_of_month(d)
        self.assertTrue(rs)

        d = datetime(year=2015, month=2, day=27)
        rs = c.check_last_day_of_month(d)
        self.assertFalse(rs)

        d = datetime(year=2016, month=2, day=29)
        rs = c.check_last_day_of_month(d)
        self.assertTrue(rs)

        d = datetime(year=2015, month=11, day=30)
        rs = c.check_last_day_of_month(d)
        self.assertTrue(rs)

        d = datetime(year=2015, month=12, day=1)
        rs = c.check_last_day_of_month(d)
        self.assertFalse(rs)

        d = datetime.now()
        rs = c.check_last_day_of_month(d)
        #self.assertFalse(rs)

    @unittest.skip("it will send a email")
    def test_lib_demail_send(self):
        email = demail.Email()
        email.send(receiver="choldrim@foxmail.com",
                CC="tangcaijun@linuxdeepin.com",
                subject="subject",
                content="hello")
        email.close()


if __name__ == "__main__":
    unittest.main()



