.. _cosi.specs.sales:

================
Product invoices
================

.. This document is part of the Lino Così test suite. To run only this
   test:

    $ python setup.py test -s tests.DocsTests.test_sales
    
    doctest init:

    >>> from lino import startup
    >>> startup('lino_cosi.projects.std.settings.doctests')
    >>> from lino.api.doctest import *
    >>> ses = rt.login('robin')

A **product invoice** is an invoice whose rows usually refer to a
*product* (and provides rules for mapping products to general accounts
if needed).  This is in contrast to *account invoices* which don't
need any products.

The plugin
==========

Lino Così implements product invoices in the
:mod:`lino_cosi.lib.sales` plugin.  The internal codename "sales" is
for historical reasons, you might generate product invoices for other
trade types as well.

The plugin --of course-- needs and automatically installs the
:mod:`lino_xl.lib.products` plugin.

It also needs and installs :mod:`lino_cosi.lib.vat` (and not
:mod:`lino_cosi.lib.vatless`).  Which means that if you want product
invoices, you cannot *not* also install the VAT framework.  If the
site owner is not subject to VAT, you can hide the VAT fields and
define a VAT rate of 0 for everything.

>>> dd.plugins.sales.needs_plugins
['lino_xl.lib.products', 'lino_cosi.lib.vat']

This plugin is needed and extended by :mod:`lino_cosi.lib.invoicing`
which adds automatic generation of such product invoices.

>>> dd.plugins.invoicing.needs_plugins
['lino_cosi.lib.sales']


Trade types
===========

The plugin updates your trade types and defines some additional
database fields to be installed by :func:`inject_tradetype_fields
<lino_cosi.lib.ledger.choicelists.inject_tradetype_fields>`.

For example the sales price of a product:

>>> print(ledger.TradeTypes.sales.price_field_name)
sales_price

>>> print(ledger.TradeTypes.sales.price_field_label)
Sales price

>>> products.Product._meta.get_field('sales_price')
<lino.core.fields.PriceField: sales_price>



The invoicing address of a partner
==================================

The plugin also injects a field :attr:`invoice_recipient
<lino.modlib.contacts.models.Partner.invoice_recipient>` to the
:class:`contacts.Partner <lino.modlib.contacts.models.Partner>` model:

.. attribute:: lino.modlib.contacts.models.Partner.invoice_recipient

  The recipient of invoices (invoicing address).



The sales journal
=================

>>> mt = contenttypes.ContentType.objects.get_for_model(sales.VatProductInvoice).id
>>> obj = sales.VatProductInvoice.objects.get(journal__ref="SLS", number=20)
>>> url = '/api/sales/InvoicesByJournal/{0}'.format(obj.id)
>>> url += '?mt={0}&mk={1}&an=detail&fmt=json'.format(mt, obj.journal.id)
>>> res = test_client.get(url, REMOTE_USER='robin')
>>> # res.content
>>> r = check_json_result(res, "navinfo data disable_delete id title")
>>> print(r['title'])
Sales invoices (SLS) » SLS 20


IllegalText: The <text:section> element does not allow text
===========================================================

The following reproduces a situation which caused above error
until :blogref:`20151111`. 

TODO: it is currently disabled for different reasons: leaves dangling
temporary directories, does not reproduce the problem (probably
because we must clear the cache).

>> obj = rt.modules.sales.VatProductInvoice.objects.all()[0]
>> obj
VatProductInvoice #1 ('SLS#1')
>> from lino.modlib.appypod.appy_renderer import AppyRenderer
>> tplfile = rt.find_config_file('sales/VatProductInvoice/Default.odt')
>> context = dict()
>> outfile = "tmp.odt"
>> renderer = AppyRenderer(ses, tplfile, context, outfile)
>> ar = rt.modules.sales.ItemsByInvoicePrint.request(obj)
>> print(renderer.insert_table(ar))  #doctest: +ELLIPSIS
<table:table ...</table:table-rows></table:table>


>> item = obj.items.all()[0]
>> item.description = """
... <p>intro:</p><ol><li>first</li><li>second</li></ol>
... <p></p>
... """
>> item.save()
>> print(renderer.insert_table(ar))  #doctest: +ELLIPSIS
Traceback (most recent call last):
...
IllegalText: The <text:section> element does not allow text


The language of an invoice
==========================

The language of an invoice not necessary that of the user who enters
the invoice. It is either the partner's :attr:`language
<lino.modlib.contacts.models.Partner.language>` or (if this is empty)
the Site's :meth:`get_default_language
<lino.core.site.Site.get_default_language>`.

