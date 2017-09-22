# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
Helper for logistics/items resources.

"""
from .manager import Manager


class LogisticsItems(Manager):
    resource = 'logistics/Items'

    def filter(self, item_code=None, **kwargs):
        # $select=ID,Code,Name
        if 'select' not in kwargs:
            kwargs['select'] = 'ID,Code,Description'

        if item_code is not None:
            remote_id = self._remote_item_code(item_code)
            self._filter_append(kwargs, u'Code eq %s' % (remote_id,))
        return super(LogisticsItems, self).filter(**kwargs)

    def _remote_item_code(self, code):
        return u"'%s'" % (code.replace("'", "''"),)
