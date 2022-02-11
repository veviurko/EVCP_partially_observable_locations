from datetime import datetime


def date_time_to_datetime(date_string, time_string):
    """ Transforms date string into datetime object """
    date_string_uni = date_string.replace('-', '.').replace('/', '.').replace('_', '.')
    date_list_of_strings = date_string_uni.split('.')
    date_list_of_ints = list(map(int, date_list_of_strings))
    date_list_of_ints[-1] = int(date_list_of_ints[-1])
    hours = int(time_string[:time_string.find(':')])
    minutes = int(time_string[time_string.find(':') + 1:])
    date_list_of_ints.insert(0, hours)
    date_list_of_ints.insert(0, minutes)
    return datetime(*reversed(date_list_of_ints))


def get_time_string(minutes):
    hour = int(minutes // 60)
    hour_str = str(hour)
    if hour < 10:
        hour_str = '0%d' % hour
    minutes = minutes % 60
    minutes_str = str(minutes)
    if minutes < 10:
        minutes_str = '0%d' % minutes
    return '%s:%s' % (hour_str, minutes_str)
