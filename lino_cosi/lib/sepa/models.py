# -*- coding: UTF-8 -*-
# Copyright 2014-2016 Luc Saffre
# This file is part of Lino Cosi.
#
# Lino Cosi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Lino Cosi is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with Lino Cosi.  If not, see
# <http://www.gnu.org/licenses/>.


"""
Database models for `lino_cosi.lib.sepa`.

"""

from __future__ import unicode_literals

from django.db import models
from lino.api import dd, _, rt
from lino.core.diff import ChangeWatcher

from lino.utils.format_date import fds

from .fields import IBANField, BICField, IBAN_FORMFIELD
from .utils import belgian_nban_to_iban_bic, iban2bic
from .roles import SepaUser, SepaStaff
from lino_xl.lib.contacts.roles import ContactsUser


@dd.python_2_unicode_compatible
class Account(dd.Model):
    """A bank account related to a given :class:`Partner
    <lino.modlib.models.contacts.Partner>`.

    One partner can have more than one bank account.

    .. attribute:: statements

        A virtual field which displays the date of the last imported
        statement for this account. Clicking on this date will open
        the `B2C account <lino_cosi.lib.b2c.models.Account>` with same
        IBAN number.

        This field is empty when no B2C Account exists.

        Available only when :mod:`lino_cosi.lib.b2c` is installed as
        well.

    """

    class Meta:
        app_label = 'sepa'
        abstract = dd.is_abstract_model(__name__, 'Account')
        verbose_name = _("Bank account")
        verbose_name_plural = _("Bank accounts")

    partner = dd.ForeignKey(
        'contacts.Partner',
        related_name='sepa_accounts', null=True, blank=True)

    iban = IBANField(verbose_name=_("IBAN"))
    bic = BICField(verbose_name=_("BIC"), blank=True)

    remark = models.CharField(_("Remark"), max_length=200, blank=True)

    primary = models.BooleanField(
        _("Primary"),
        default=False,
        help_text=_(
            "Enabling this field will automatically disable any "
            "previous primary account and update "
            "the partner's IBAN and BIC"))

    allow_cascaded_delete = ['partner']

    def __str__(self):
        return IBAN_FORMFIELD.prepare_value(self.iban)
        # if self.remark:
        #     return "{0} ({1})".format(self.iban, self.remark)
        # return self.iban

    def full_clean(self):
        if self.iban and not self.bic:
            if self.iban[0].isdigit():
                iban, bic = belgian_nban_to_iban_bic(self.iban)
                self.bic = bic
                self.iban = iban
            else:
                self.bic = iban2bic(self.iban) or ''
        super(Account, self).full_clean()

    def after_ui_save(self, ar, cw):
        super(Account, self).after_ui_save(ar, cw)
        if self.primary:
            mi = self.partner
            for o in mi.sepa_accounts.exclude(id=self.id):
                if o.primary:
                    o.primary = False
                    o.save()
                    ar.set_response(refresh_all=True)
            watcher = ChangeWatcher(mi)
            for k in PRIMARY_FIELDS:
                setattr(mi, k, getattr(self, k))
            mi.save()
            watcher.send_update(ar.request)

    @dd.displayfield(_("Statements"))
    def statements(self, ar):
        if ar is None or not dd.is_installed('b2c'):
            return ''
        Account = rt.modules.b2c.Account
        try:
            b2c = Account.objects.get(iban=self.iban)
        except Account.DoesNotExist:
            return ''
        return ar.obj2html(b2c, fds(b2c.last_transaction))


PRIMARY_FIELDS = dd.fields_list(Account, 'iban bic')


class Accounts(dd.Table):
    required_roles = dd.login_required(SepaStaff)
    model = 'sepa.Account'


class AccountsByPartner(Accounts):
    """Show the bank account(s) defined for a given partner. To be
    included to a detail window on partner.

    """
    required_roles = dd.login_required((ContactsUser, SepaUser))
    master_key = 'partner'
    column_names = 'iban bic remark primary *'
    order_by = ['iban']
    stay_in_grid = True
    auto_fit_column_widths = True
    insert_layout = """
    iban bic
    remark
    """
