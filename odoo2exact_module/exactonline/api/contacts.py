# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
Helper for contacts/Contactpersonen resources.
For Dacom we use the field SocialSecurity (string) as identifier
This file is not part of the Exact Online REST API Library in Python
but added by Allard Lamberink, Dacom B.V.
"""
from .manager import Manager


class Contacts(Manager):
    resource = 'crm/Contacts'

    def filter(self, contact_bsn=None, **kwargs):
        # $select=ID,SocialSecurityNumber,LastName
        if 'select' not in kwargs:
            kwargs['select'] = 'ID,SocialSecurityNumber,LastName,Modified'

        if contact_bsn is not None:
            remote_id = self._remote_contact_bsn(contact_bsn)
            self._filter_append(kwargs, u'SocialSecurityNumber eq %s' % (remote_id,))
        return super(Contacts, self).filter(**kwargs)

    def _remote_contact_bsn(self, contact_bsn):
        return u"'%18s'" % (contact_bsn.replace("'", "''"),)
