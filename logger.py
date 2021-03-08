"""Build logger"""
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d: %(message)s',
    '%Y-%m-%d %H:%M:%S')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
