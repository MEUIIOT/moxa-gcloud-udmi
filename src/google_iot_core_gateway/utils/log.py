import logging
from colorlog import ColoredFormatter

"""
# Change log

Date: 02 Dec 2021: 
    - Disabled colored log Feature
    - Disabled logging into logfile to avoid disk space full problem 
"""

def setup_logger():
    """
        Set ups logger for this module.
        Returns:
            Logger with established formatter.
        """

    log_format = '%(asctime)s: %(levelname)s - %(module)s - %(message)s'
    formatter = logging.Formatter(log_format)

    color_format = ColoredFormatter(
        "%(asctime)s: %(log_color)s %(levelname) - 2s%(reset)s - %(module)s - %(message)s",
        datefmt="[%Y-%m-%d %H:%M:%S]",
        reset=False,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red', })

    # Save full log
    #logging.basicConfig(level=logging.DEBUG, datefmt="[%Y-%m-%d %H:%M:%S]", format=log_format, filename='main.log',
    #                    filemode="w")
    logging.basicConfig(level=logging.DEBUG, datefmt="[%Y-%m-%d %H:%M:%S]", format=log_format)              

    logger = logging.getLogger()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(color_format)
    #logger.addHandler(console_handler)

    #error_handler = logging.FileHandler('error.log')
    #error_handler.setLevel(logging.ERROR)
    #error_handler.setFormatter(formatter)
    #logger.addHandler(error_handler)

    return logger


def update_logger_verbose_level(logger, verbose_level):
    if verbose_level == '1':
        #logger.handlers[1].setLevel(logging.WARN)
        logger.setLevel(logging.WARN)
        logger.info("Enabled Warning Mode".format(verbose_level))
    elif verbose_level == '2':
        #logger.handlers[1].setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.info("Enabled Debug Mode".format(verbose_level))
    elif verbose_level == '3':
        #logger.handlers[1].setLevel(logging.INFO)
        logger.setLevel(logging.INFO)
        logger.info("Enabled Info Mode".format(verbose_level))
