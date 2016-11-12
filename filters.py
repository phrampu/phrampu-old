import logging


class MyFilter(logging.Filter):

    def filter(self, record):
        return record.name != 'paramiko.transport'
