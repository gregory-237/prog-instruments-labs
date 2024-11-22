import logging

from config import DEFAULT_EXTRA_FIELDS


class CustAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra_fields = {}
        for key in ['user_id', 'role', 'ext_params']:
            extra_fields[key] = kwargs.pop(key, self.extra[key])
        kwargs['extra'] = extra_fields
        return msg, kwargs


logger = logging.getLogger('actions')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('logs.log', encoding='utf-8')
formatter = logging.Formatter(
    fmt='%(asctime)s\t%(message)s\t%(user_id)s\t%(role)s\t%(ext_params)s',
    datefmt='%d.%m.%Y %H:%M:%S',
)
handler.setFormatter(formatter)
logger.addHandler(handler)

configured_logger = CustAdapter(logger, DEFAULT_EXTRA_FIELDS)