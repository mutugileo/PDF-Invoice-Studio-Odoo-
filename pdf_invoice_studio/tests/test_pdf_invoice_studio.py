# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'pdf_invoice_studio')
class TestPdfInvoiceStudio(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Acme Global Corp',
            'street': '100 Market St',
            'city': 'San Francisco',
            'zip': '94105',
            'country_id': cls.env.ref('base.us').id,
            'vat': 'US123456789',
        })
        cls.partner_shipping_different = cls.env['res.partner'].create({
            'name': 'Acme Warehouse East',
            'parent_id': cls.partner_a.id,
            'type': 'delivery',
            'street': '500 Logistics Blvd',
            'city': 'Oakland',
            'zip': '94607',
            'country_id': cls.env.ref('base.us').id,
        })
        cls.partner_shipping_identical = cls.env['res.partner'].create({
            'name': 'Acme HQ Delivery Dock',
            'parent_id': cls.partner_a.id,
            'type': 'delivery',
            'street': '100 Market St',
            'city': 'San Francisco',
            'zip': '94105',
            'country_id': cls.env.ref('base.us').id,
        })

    def test_01_company_settings_persistence(self):
        """Verify custom branding and compliance fields persist on res.company."""
        self.company.write({
            'invoice_title': 'COMMERCIAL TAX INVOICE',
            'business_registration_number': 'REG-2026-X99',
            'tax_id_label': 'KRA PIN',
            'shipping_address_mode': 'auto',
            'primary_color': '#2563eb',
            'secondary_color': '#eff6ff',
            'payment_instructions': '<p>Bank: Chase<br/>IBAN: US99CHAS1234567890</p>',
            'invoice_footer_note': 'Terms: Net 30 Days. Thank you.',
            'authorized_signatory_name': 'Sarah Connor',
            'authorized_signatory_title': 'Chief Financial Officer',
        })

        self.assertEqual(self.company.invoice_title, 'COMMERCIAL TAX INVOICE')
        self.assertEqual(self.company.business_registration_number, 'REG-2026-X99')
        self.assertEqual(self.company.tax_id_label, 'KRA PIN')
        self.assertEqual(self.company.shipping_address_mode, 'auto')
        self.assertEqual(self.company.primary_color, '#2563eb')
        self.assertEqual(self.company.authorized_signatory_name, 'Sarah Connor')

    def test_02_dynamic_address_collapsing_logic(self):
        """Verify address matching logic for dynamic collapsing."""
        # Invoice with no separate delivery partner
        invoice_same = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'partner_shipping_id': self.partner_a.id,
        })
        self.assertTrue(invoice_same.is_shipping_identical_to_billing())

        # Invoice with delivery partner having identical address fields
        invoice_identical_fields = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'partner_shipping_id': self.partner_shipping_identical.id,
        })
        self.assertTrue(invoice_identical_fields.is_shipping_identical_to_billing())

        # Invoice with delivery partner having different address fields
        invoice_different = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'partner_shipping_id': self.partner_shipping_different.id,
        })
        self.assertFalse(invoice_different.is_shipping_identical_to_billing())

    def test_03_sanitized_filename_generation(self):
        """Verify filesystem-safe filename generation for exported PDFs."""
        invoice = self.env['account.move'].create({
            'name': 'INV/2026/00042#Test',
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
        })
        filename = invoice.get_sanitized_invoice_filename()
        self.assertTrue(filename.endswith('.pdf'))
        self.assertNotIn('/', filename)
        self.assertNotIn('#', filename)
        self.assertIn('INV_2026_00042_Test', filename)
        self.assertIn('Acme_Global_Corp', filename)

    def test_04_bulk_zip_export_action(self):
        """Verify bulk zip export action validation and URL generation."""
        # Draft invoice should fail validation
        draft_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
        })
        with self.assertRaises(UserError):
            draft_invoice.action_export_invoices_zip()

        # Simulate posted invoice
        draft_invoice.state = 'posted'
        draft_invoice.name = 'INV/2026/00099'
        action = draft_invoice.action_export_invoices_zip()

        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertIn(f'/pdf_invoice_studio/download_zip?move_ids={draft_invoice.id}', action.get('url'))
