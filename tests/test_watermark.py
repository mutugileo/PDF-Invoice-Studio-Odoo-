# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'pdf_invoice_studio')
class TestInvoiceWatermark(TransactionCase):
    """Status stamp shown on the invoice.

    Odoo Community has no watermark of any kind, so all of this behaviour is
    ours and needs pinning - especially the precedence, where a wrong answer
    puts OVERDUE on an invoice the customer already paid.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({'name': 'Acme Global Corp'})
        cls.product = cls.env['product.product'].create({
            'name': 'Consulting',
            'list_price': 1000.0,
        })

    def _invoice(self, due_date=None, post=False):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date_due': due_date,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })
        if post:
            invoice.action_post()
        return invoice

    def test_01_draft_is_stamped(self):
        self.assertEqual(self._invoice().get_invoice_watermark(), 'DRAFT')

    def test_02_posted_unpaid_not_yet_due_has_no_stamp(self):
        future = fields.Date.context_today(self.env.user) + timedelta(days=30)
        invoice = self._invoice(due_date=future, post=True)

        self.assertEqual(invoice.get_invoice_watermark(), '')

    def test_03_overdue_is_stamped(self):
        past = fields.Date.context_today(self.env.user) - timedelta(days=10)
        invoice = self._invoice(due_date=past, post=True)

        self.assertEqual(invoice.get_invoice_watermark(), 'OVERDUE')

    def test_04_cancelled_beats_everything(self):
        past = fields.Date.context_today(self.env.user) - timedelta(days=10)
        invoice = self._invoice(due_date=past, post=True)
        invoice.button_cancel()

        self.assertEqual(invoice.get_invoice_watermark(), 'CANCELLED')

    def test_05_paid_beats_overdue(self):
        """An invoice paid after its due date must read PAID, never OVERDUE."""
        past = fields.Date.context_today(self.env.user) - timedelta(days=10)
        invoice = self._invoice(due_date=past, post=True)
        self.assertEqual(invoice.get_invoice_watermark(), 'OVERDUE')

        # Register the full payment through the standard wizard.
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids
        ).create({})
        wizard._create_payments()

        self.assertEqual(invoice.payment_state, 'paid')
        self.assertEqual(invoice.get_invoice_watermark(), 'PAID')

    def test_06_master_switch_suppresses_all_stamps(self):
        self.company.invoice_watermark_enabled = False

        self.assertEqual(self._invoice().get_invoice_watermark(), '')

    def test_07_per_status_toggle_suppresses_only_that_stamp(self):
        self.company.invoice_watermark_show_draft = False
        self.assertEqual(self._invoice().get_invoice_watermark(), '')

        past = fields.Date.context_today(self.env.user) - timedelta(days=10)
        self.assertEqual(
            self._invoice(due_date=past, post=True).get_invoice_watermark(),
            'OVERDUE',
        )

    def test_08_intensity_blends_into_the_colour(self):
        """Intensity is baked into the hex, not applied as CSS opacity.

        wkhtmltopdf ignores opacity on this element and prints the stamp solid,
        so a subtle setting has to reach the renderer as an already-pale colour.
        """
        invoice = self._invoice()
        self.company.invoice_watermark_color = '#d92d20'

        self.company.invoice_watermark_intensity = 'subtle'
        subtle = invoice.get_invoice_watermark_color()

        self.company.invoice_watermark_intensity = 'bold'
        bold = invoice.get_invoice_watermark_color()

        self.assertNotEqual(subtle, bold)
        # Subtle must sit closer to white than bold does.
        to_int = lambda h: sum(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
        self.assertGreater(to_int(subtle), to_int(bold))
        # And neither may be the raw colour, or opacity was silently lost.
        self.assertNotEqual(bold.lower(), '#d92d20')

    def test_07a_font_size_scales_down_for_longer_stamps(self):
        """Longer wording must print smaller, or it runs off the page.

        A single size fails both ways: 58px left OVERDUE lost on a dense 30-line
        invoice, and PARTIALLY PAID clips long before the size that fixes that.
        Both bounds were established from printed A4 output.
        """
        past = fields.Date.context_today(self.env.user) - timedelta(days=10)
        overdue = self._invoice(due_date=past, post=True)      # OVERDUE, 7 chars
        self.assertEqual(overdue.get_invoice_watermark(), 'OVERDUE')
        short_size = overdue.get_invoice_watermark_font_size()

        # A real partial payment, so the longest stamp is genuinely produced
        # rather than asserted against a hand-written string. The due date is in
        # the future on purpose: OVERDUE outranks PARTIALLY PAID, so an overdue
        # part-paid invoice would stamp OVERDUE and never exercise this band.
        future = fields.Date.context_today(self.env.user) + timedelta(days=30)
        partial = self._invoice(due_date=future, post=True)
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=partial.ids
        ).create({})
        wizard.amount = partial.amount_total / 4.0
        wizard._create_payments()

        self.assertEqual(partial.payment_state, 'partial')
        self.assertEqual(partial.get_invoice_watermark(), 'PARTIALLY PAID')
        long_size = partial.get_invoice_watermark_font_size()

        self.assertLess(
            long_size, short_size,
            "the longest stamp must print smaller, or it clips off the page edge",
        )

    def test_08a_bold_stays_light_enough_to_read_through(self):
        """Even the strongest stamp must not darken enough to obscure figures.

        At alpha 0.70 the outline cut through the amount column on a printed
        invoice badly enough to degrade "$ 11,750.00". The ceiling was lowered
        after checking real PDFs; this pins it so it cannot drift back up.
        """
        invoice = self._invoice()
        self.company.invoice_watermark_color = '#000000'  # worst case: pure black
        self.company.invoice_watermark_intensity = 'bold'

        blended = invoice.get_invoice_watermark_color().lstrip('#')
        channels = [int(blended[i:i + 2], 16) for i in (0, 2, 4)]

        # Every channel must retain substantial white, so the stroke stays a tint
        # rather than a solid dark line across the amounts.
        for value in channels:
            self.assertGreaterEqual(
                value, 100,
                f"bold watermark too dark ({blended}) - it will obscure invoice figures",
            )

    def test_08b_malformed_colour_falls_back(self):
        """A bad hex must not break the render."""
        invoice = self._invoice()

        for bad in ('', 'not-a-colour', '#12', 'zzzzzz'):
            self.company.invoice_watermark_color = bad
            result = invoice.get_invoice_watermark_color()
            self.assertRegex(result, r'^#[0-9a-f]{6}$')

    def test_08c_short_hex_is_expanded(self):
        invoice = self._invoice()
        self.company.invoice_watermark_color = '#f00'
        self.company.invoice_watermark_intensity = 'bold'

        self.assertRegex(invoice.get_invoice_watermark_color(), r'^#[0-9a-f]{6}$')

    def test_09_watermark_renders_into_the_document(self):
        past = fields.Date.context_today(self.env.user) - timedelta(days=10)
        invoice = self._invoice(due_date=past, post=True)
        self.company.invoice_watermark_color = '#d92d20'

        html, _content_type = self.env['ir.actions.report']._render_qweb_html(
            'account.report_invoice', [invoice.id]
        )
        html = html.decode() if isinstance(html, bytes) else html

        self.assertIn('OVERDUE', html)
        self.assertIn('pis-watermark', html)
        # The blended colour reaches the document, not the raw one, and no CSS
        # opacity is emitted (the PDF engine ignores it).
        self.assertIn(invoice.get_invoice_watermark_color(), html)
        self.assertNotIn('opacity:', html.split('pis-watermark')[1][:400])

    def test_10_no_watermark_markup_when_disabled(self):
        self.company.invoice_watermark_enabled = False
        invoice = self._invoice(post=True)

        html, _content_type = self.env['ir.actions.report']._render_qweb_html(
            'account.report_invoice', [invoice.id]
        )
        html = html.decode() if isinstance(html, bytes) else html

        self.assertNotIn('pis-watermark', html)
