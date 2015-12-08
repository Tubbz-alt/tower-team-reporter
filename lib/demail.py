import os
import smtplib
from configparser import ConfigParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_CONF_PATH = "%s/.AutoScriptConfig/tower-team-reporter/email.ini" % os.getenv("HOME")

class Email:
    def __smtp(self, server, username, passwd):
        try:
            smtp = smtplib.SMTP()
            smtp.connect(server)
            smtp.login(username, passwd)
            smtp.helo()
            return smtp
        except Exception as e:
            print("E: connect mailing service fail")
            raise e

    def get_user_info(self):
        config = ConfigParser()
        config.read(EMAIL_CONF_PATH)
        server = config["USER"]["SMTPServer"]
        username = config["USER"]["UserName"]
        passwd = config["USER"]["UserPWD"]
        return server, username, passwd


    def __init__(self):
        (server, username, passwd) = self.get_user_info()
        self.smtp = self.__smtp(server, username, passwd)
        self.sender = username

    def close(self):
        self.smtp.quit()

    def send(self, receiver, subject, content, CC=""):

        root = MIMEMultipart()
        root["Subject"] = subject
        root["From"] = self.sender
        root["To"] = receiver
        if CC:
            root["Cc"] = CC

        footer = """
        <br>
        <br>
        <hr>
        <footer>
          <p>Posted by: <a href="https://ci.deepin.io">deepin AutomatedScript ci</a></p>
          <p>Contact: <a href="mailto:tangcaijun@linuxdeepin.com">tangcaijun@linuxdeepin.com</a></p>
        </footer>
        """

        content_part = MIMEText(content + footer, "html", "utf-8")
        root.attach(content_part)

        if CC:
            all_receivers = receiver.split(",") + CC.split(",")
        else:
            all_receivers = receiver.split(",")

        self.smtp.sendmail(self.sender, all_receivers, root.as_string())

        #self.close()


