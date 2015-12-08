#!/usr/bin/python3

import argparse
import json
import re
import time


from configparser import ConfigParser
from datetime import datetime
from datetime import timedelta
from pprint import pprint

from pyvirtualdisplay import Display
from selenium import webdriver

from lib import demail

DEBUG = False
LAST_DAY = False

USER_CONF_PATH = "user.ini"
CONTACT_CONF_PATH = "team.json"

TEMPLATE = """
<p>你好:</p>
<p>&nbsp;&nbsp;&nbsp;&nbsp;"%s" 团队当前的成员如下：</p>
<p>%s</p>
<br>
<p>若本组成员信息有误，请使用“回复全部”，说明情况。</p>
"""


class Browser_Controller:

    def __init__(self):
        self.browser = webdriver.Firefox()
        self.team_url = "https://tower.im/teams/35e3a49a6e2e40fa919070f0cd9706c8/members/"
        self.defaul_url = self.team_url
        (username, passwd) = self.get_login_info()
        self.login(username, passwd)
        self.browser.get(self.defaul_url)


    def get_login_info(self):
        config = ConfigParser()
        config.read(USER_CONF_PATH)
        username = config["USER"]["UserName"]
        passwd = config["USER"]["UserPWD"]
        return username, passwd


    def login(self, username, passwd):

        login_url = "https://tower.im/users/sign_in"
        self.browser.get(login_url)
        unEL = self.browser.find_element_by_id("email")
        pwdEL = self.browser.find_element_by_name("password")
        unEL.send_keys(username)
        pwdEL.send_keys(passwd)
        unEL.submit()

        time.sleep(5)

        # check login status
        if self.browser.current_url == self.defaul_url:
            print ("login successfully")
            return True

        # fuck tower....
        elif self.browser.current_url == "https://tower.im/teams/35e3a49a6e2e40fa919070f0cd9706c8/projects/":
            print ("login successfully")
            return True

        else:
            print ("login error, current url (%s) does not match." % self.browser.current_url)
            return False


    def get_group_members(self, guid):
        # format: {guid: [member_A, member_B, member_C]}
        members = []
        member_count_script = 'return $(".group[data-guid=%s]  .member .name").length' % guid
        member_count = self.browser.execute_script(member_count_script)
        for i in range(0, member_count):
            script = 'return $($(".group[data-guid=%s] .member .name")[%d]).text()' % (guid, i)
            member = self.browser.execute_script(script)
            members.append(member)
        return members


    def get_all_group_guids(self):
        # format: [group_guid_A, group_guid_B, group_guid_C]
        guids = []
        group_count_script = 'return $(".group").length'
        group_count = self.browser.execute_script(group_count_script)
        for i in range(0, group_count):
            script = 'return $($(".group")[%d]).attr("data-guid")' %i
            guid = self.browser.execute_script(script)
            if guid == "0":
                continue
            guids.append(guid)
        return guids


    def get_all_groups_data(self):
        # dict format: {g_guid: [member_A, member_B], g_guid: [member_A, member_B]}
        all_group_members = {}
        guids = self.get_all_group_guids()
        for guid in guids:
            members = self.get_group_members(guid)
            all_group_members[guid] = members

        return all_group_members


class Controller:

    def __init__(self):
        display = Display(visible=0, size=(1366, 768))
        display.start()

    def work(self):
        now = datetime.now()
        team_info = self.get_team_info()
        # test
        #team_info = {"79d4b0d56cac41bd931fc772365772c4": ['刘文欢', '王棣', '颜新兴', '张磊', '朱敏']}
        team_info_all_list = self.fill_team_info_with_contact(team_info)
        pprint(team_info_all_list)
        if self.check_last_day_of_month(now):
            print(">>>> sending email....")
            if not DEBUG:
                self.send_mail(team_info_all_list)
            else:
                print("debug mode, skip sending email.")
            print("<<<< finish sending email....")
        else:
            print("Sorry, I can only work on the last day of every month, abort sending emails.")

    def get_team_info(self):
        b = Browser_Controller()
        team_info = b.get_all_groups_data()
        return team_info

    def generate_email_content(self, team_info):
        # team_info: {name: name, guid: guid, members:[], cc: [], recipients: []}
        members = ", ".join(team_info.get("members", []))
        content = TEMPLATE % (team_info.get("name"), members)
        return content


    def send_mail(self, all_teams_info):
        # team_info_all format: [{name: name, guid: guid, members:[], cc: [], recipients: []}]
        email = demail.Email()
        now = datetime.now()
        for team in all_teams_info:
            subject = "%s-%s \"%s\" 团队成员信息" % (now.year, now.month, team.get("name"))
            content = self.generate_email_content(team)
            if len(team.get("cc")):
                email.send(receiver=",".join(team.get("recipients")),
                        CC=",".join(team.get("cc")),
                        subject=subject,
                        content=content)
            else:
                email.send(receiver=",".join(team.get("recipients")),
                        subject=subject,
                        content=content)
        email.close()


    def get_contact_data(self):

        contact_data = {}
        with open(CONTACT_CONF_PATH) as fp:
            contact_data = json.load(fp)

        return contact_data


    def fill_team_info_with_contact(self, team_info):

        # format: [{name: name, guid: guid, members:[], cc: [], recipients: []}]
        team_info_with_contact = []
        contact_data = self.get_contact_data()
        for guid, members in team_info.items():

            # populate contacts to group data
            for item in contact_data.get("teams"):

                # match group
                if item.get("guid") == guid:
                    team = {}
                    team["guid"] = guid
                    team["recipients"] = contact_data.get("common_recipients").copy()
                    team["members"] = members.copy()
                    cc_list = contact_data.get("common_cc").copy()
                    team["name"] = item.get("name")

                    # append extra contact
                    team["recipients"] += item.get("recipients")
                    cc_list += item.get("cc")

                    # filter recipients
                    team["recipients"] = list(set(team["recipients"]))

                    # filter cc
                    team["cc"] = list([cc for cc in cc_list if cc not in team["recipients"]])

                    team_info_with_contact.append(team)

        return team_info_with_contact

    def check_last_day_of_month(self, date):
        if LAST_DAY:
            return True
        delta = timedelta(days=1)
        tomorrow = date + delta
        if tomorrow.day == 1:
            return True
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="a team info collector")

    parser.add_argument("--debug", dest="debug", action="store_true",
            help="debug mode, will not send email")

    parser.add_argument("--last-day", dest="last_day", action="store_true",
            help="always return True when checking last day of month")

    args = parser.parse_args()
    DEBUG = args.debug
    LAST_DAY = args.last_day

    c = Controller()
    c.work()

