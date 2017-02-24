from openerp.osv import osv, fields
from base_file_protocol import FileCsvWriter
from tempfile import TemporaryFile

class StockVendorReceipt(osv.osv):
    _inherit = 'stock.vendor.receipt'

    def export_receipt(self, cr, uid, ids, context=None):
        receipt = self.browse(cr, uid, ids[0])
	fieldnames = ['product_id', 'Sku', 'Packslip Qty', 'Qty on Dock', 'Qty to Receive', 'Cost'
	]

	output_file = TemporaryFile('w+b')
        csv = FileCsvWriter(output_file, fieldnames, encoding="utf-8", writeheader=True, delimiter=',', \
                            quotechar='"')
	
	for line in receipt.items:
	    row = {
		'product_id': line.product.id,
		'Sku': line.product.default_code,
		'Packslip Qty': line.receipt_qty,
		'Qty on Dock': line.qty_pending_dock,
		'Qty to Receive': 0,
		'Cost': 0,
	    }
	    csv.writerow(row)


        return self.pool.get('pop.up.file').open_output_file(cr, uid, receipt.name + '.csv', output_file, \
                                'Vendor Receipt Export', context=context)
	
