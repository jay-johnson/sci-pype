GRAY_COLOR          = '\x1b[37m'
BLUE_COLOR          = '\x1b[36m'
PURPLE_COLOR        = '\x1b[35m'
YELLOW_COLOR        = '\x1b[33m'
GREEN_COLOR         = '\x1b[32m'
FAIL_COLOR          = '\x1b[31m'
END_COLOR           = '\x1b[0m'


def blue_print(msg):
    print "" + BLUE_COLOR + str(msg) + END_COLOR
    return None
# end of blue_print


def purple_print(msg):
    print "" + PURPLE_COLOR + str(msg) + END_COLOR
    return None
# end of purple_print


def gray_print(msg):
    print "" + GRAY_COLOR + str(msg) + END_COLOR
    return None
# end of gray_print


def yellow_print(msg):
    print "" + YELLOW_COLOR + str(msg) + END_COLOR
    return None
# end of yellow_print


def green_print(msg):
    print "" + GREEN_COLOR + str(msg) + END_COLOR
    return None
# end of green_print


def red_print(msg):
    print "" + FAIL_COLOR + str(msg) + END_COLOR
    return None
# end of red_print


def lg(msg, color_num=6):
    if color_num == 0:
        red_print(msg)
    elif color_num == 1:
        blue_print(msg)
    elif color_num == 2:
        yellow_print(msg)
    elif color_num == 3:
        purple_print(msg)
    elif color_num == 4:
        gray_print(msg)
    elif color_num == 5:
        green_print(msg)
    else:
        print (msg)

    return None
# end of lg


