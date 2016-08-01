import json, datetime, os, traceback, sys

class SlkMsg:


    def __init__(self, config_data):

        self.m_config = config_data

        self.m_bot_name = self.m_config["BotName"]
        self.m_slack_channel = self.m_config["ChannelName"]
        self.m_notify_user = self.m_config["NotifyUser"]
        self.m_env_name = self.m_config["EnvName"]
        self.m_slack_token = self.m_config["Token"]

    # end of __init__


    def handle_send_slack_internal_ex(self, ex):

        try:

            exc_type, exc_obj, exc_tb = sys.exc_info()
            header_str = datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S") + " @" + str(self.m_notify_user) + " `" + str(self.m_env_name) + "` *" + str(ex) + "*\n"
            ex_error = self.get_exception_error_message(ex, exc_type, exc_obj, exc_tb)
            send_slack_msg = header_str + str(ex_error) + "\n"
            self.post_message_to_slack("#" + str(self.m_slack_channel), send_slack_msg)

        except Exception,k:
            print "ERROR: Failed to Send Slack Error with Ex(" + str(k) + ")"

        return None
    # end of handle_send_slack_internal_ex


    def get_exception_error_message(self, ex, exc_type, exc_obj, exc_tb):

        path_to_file = str(exc_tb.tb_frame.f_code.co_filename)
        last_line = int(exc_tb.tb_lineno)
        gh_line_number = int(last_line) - 1
        file_name = str(os.path.split(exc_tb.tb_frame.f_code.co_filename)[1])
        path_to_file = str(exc_tb.tb_frame.f_code.co_filename)
        py_file = open(path_to_file).readlines()
        line = ""
        for line_idx,cur_line in enumerate(py_file):
            if line_idx == gh_line_number:
                line = cur_line

        if str(exc_obj.message) != "":
            ex_details_msg = str(exc_obj.message)
        else:
            ex_details_msg = str(ex)

        send_error_log_to_slack = ""
        if line != "":
            send_error_log_to_slack = " File: *" + str(path_to_file) + "* on Line: *" + str(last_line) + "* Code: \n```" + str(line) + "``` \n"
        else:
            send_error_log_to_slack = "Error on Line Number: " + str(last_line)

        return send_error_log_to_slack
    # end of get_exception_error_message


    def post_message_to_slack(self, channel, message, debug=False):

        slack_response  = {}

        try:

            # SlackHQ Repository for integrating with the Slack API:
            # https://github.com/slackhq/python-slackclient         
            import slackclient

            slack = slackclient.SlackClient(self.m_slack_token)

            slack_response = slack.api_call("chat.postMessage", channel=channel, text=message, username=self.m_bot_name, as_user=True)

            if "error" in slack_response:
                print "\nERROR: Slack API call had an error(" + str(slack_response["error"]) + ")\n"

        except Exception, e:
            err_msg = "Failed to post message to slack with Ex(" + str(e) + ") SlackResponse(" + str(slack_response) + ")"
            print "ERROR: " + str(err_msg)
        # end of try/ex

    # end of post_message_to_slack


# end of SlkMsg
