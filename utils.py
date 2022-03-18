from datetime import datetime


def print_progress_bar(iteration, total, prefix='', suffix='', elapsed_second=0, decimals=1, length=100,
                       fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix} [time: {get_elapsed_time(elapsed_second)}]', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def get_elapsed_time(elapsed_second):
    if elapsed_second < 60:
        return f'{elapsed_second}s'
    elif elapsed_second < 3600:
        return f'{int(elapsed_second/60)}m {elapsed_second%60}s'
    else:
        return f'{int(elapsed_second/3600)}h {int(int(elapsed_second%3600)/60)}m {int(elapsed_second%60)}s'


def timestamp_pretty(timestamp):
    date_time = datetime.fromtimestamp(timestamp)
    date_str = date_time.strftime("%m/%d/%Y, %H:%M:%S")
    return date_str