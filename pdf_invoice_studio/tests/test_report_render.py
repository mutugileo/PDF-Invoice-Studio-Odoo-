# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

# 1x1 transparent PNG, enough to exercise the image_data_uri branches.
TINY_PNG = (
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4'
    b'//8/AwAI/AL+XJ/PwAAAAABJRU5ErkJggg=='
)


@tagged('post_install', '-at_install', 'pdf_invoice_studio')
class TestPdfInvoiceStudioRender(TransactionCase):
    """Renders the inherited invoice template.

    The other tests exercise helper methods only, so nothing covered the template
    itself - which is the actual product. Rendering to HTML rather than PDF keeps
    this runnable without wkhtmltopdf installed, and still executes every xpath,
    t-if branch and field reference the template declares.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'invoice_title': 'COMMERCIAL TAX INVOICE',
            'business_registration_number': 'REG-2026-X99',
            'tax_id_label': 'KRA PIN',
            'vat': 'KE0012345678',
            'show_tax_id': True,
            'show_company_registry': True,
            'show_billing_address': True,
            'primary_color': '#2563eb',
            'payment_instructions': '<p>Bank: Chase<br/>IBAN: US99CHAS1234567890</p>',
            'invoice_footer_note': 'Terms: Net 30 Days.',
            'authorized_signatory_name': 'Sarah Connor',
            'authorized_signatory_title': 'CFO',
            'authorized_signature': TINY_PNG,
            'company_stamp': TINY_PNG,
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Acme Global Corp',
            'street': '100 Market St',
            'city': 'San Francisco',
            'zip': '94105',
            'country_id': cls.env.ref('base.us').id,
            'vat': 'US123456789',
        })
        cls.shipping_far = cls.env['res.partner'].create({
            'name': 'Acme Warehouse East',
            'parent_id': cls.partner.id,
            'type': 'delivery',
            'street': '500 Logistics Blvd',
            'city': 'Oakland',
            'zip': '94607',
            'country_id': cls.env.ref('base.us').id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Consulting',
            'list_price': 1000.0,
        })

    def _posted_invoice(self, shipping_partner):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'partner_shipping_id': shipping_partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 3,
                'price_unit': 1000.0,
            })],
        })
        invoice.action_post()
        return invoice

    def _render(self, invoice):
        html, _content_type = self.env['ir.actions.report']._render_qweb_html(
            'account.report_invoice', [invoice.id]
        )
        return html.decode() if isinstance(html, bytes) else html

    def test_01_branding_fields_render(self):
        """Every configured branding field reaches the rendered document."""
        html = self._render(self._posted_invoice(self.shipping_far))

        self.assertIn('COMMERCIAL TAX INVOICE', html)
        self.assertIn('KRA PIN', html)
        self.assertIn('KE0012345678', html)
        self.assertIn('REG-2026-X99', html)
        self.assertIn('#2563eb', html)
        self.assertIn('Net 30 Days', html)
        self.assertIn('Sarah Connor', html)
        self.assertIn('CFO', html)

    def test_02_payment_instructions_render_unescaped(self):
        """Html field renders as markup, not escaped source.

        Guards the t-raw -> t-out migration: t-out escapes a plain str, so if the
        field ever stops returning Markup the bank details would render as visible
        tags instead of formatted text.
        """
        html = self._render(self._posted_invoice(self.shipping_far))

        self.assertIn('US99CHAS1234567890', html)
        self.assertNotIn('&lt;p&gt;Bank: Chase', html)

    def test_03_signature_and_stamp_embed_as_images(self):
        """Stamp and signature are embedded, so the PDF makes no outbound request."""
        html = self._render(self._posted_invoice(self.shipping_far))

        self.assertGreaterEqual(html.count('data:image/png;base64'), 2)

    def test_04_shipping_block_shown_when_addresses_differ(self):
        html = self._render(self._posted_invoice(self.shipping_far))

        self.assertIn('Billed To', html)
        self.assertIn('Shipped To', html)

    def test_05_shipping_block_collapses_when_addresses_match(self):
        """Auto mode hides the shipping block and widens billing to full width."""
        self.company.shipping_address_mode = 'auto'
        html = self._render(self._posted_invoice(self.partner))

        self.assertIn('Billed To', html)
        self.assertNotIn('Shipped To', html)
        self.assertIn('col-12', html)

    def test_06_shipping_block_hidden_in_never_mode(self):
        self.company.shipping_address_mode = 'never'
        html = self._render(self._posted_invoice(self.shipping_far))

        self.assertNotIn('Shipped To', html)

    def test_07_billing_block_can_be_hidden(self):
        self.company.show_billing_address = False
        html = self._render(self._posted_invoice(self.shipping_far))

        self.assertNotIn('Billed To', html)

    def test_08_branded_block_renders_with_no_shipping_partner(self):
        """Third core branch: no shipping partner at all.

        account.report_invoice_document has three separate address branches. Each
        one has to be overridden, or the branding silently falls back to Odoo's
        stock address block on perfectly ordinary invoices.
        """
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'partner_shipping_id': False,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 500.0,
            })],
        })
        invoice.action_post()
        html = self._render(invoice)

        self.assertIn('Billed To', html)
        self.assertIn('KRA PIN', html)
