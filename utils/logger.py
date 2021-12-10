import logging  # 引入logging模块


logger = logging.getLogger("Colorize Debug")
logger.setLevel(logging.DEBUG)
cli_hander = logging.StreamHandler()
cli_formatter = logging.Formatter(
    '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
cli_hander.setFormatter(cli_formatter)
logger.addHandler(cli_hander)