from openerp.osv import osv, fields
from openerp.tools.translate import _


class StockUpdateLotsFromReceiptWizard(osv.osv):
    _name = 'stock.update.lots.from.receipt.wizard'
    _columns = {
	'name': fields.char('Name'),
	'receipt': fields.many2one('stock.vendor.receipt', 'Receipt'),
	'vendor':fields.many2one('res.partner', 'Vendor'),
        'state': fields.selection([('draft', 'Draft'),
                        ('checkin', 'Ready to Count'),
                        ('verification', 'Pending Verification'),
                        ('exception', 'Exception'),
                        ('putaway', 'Pending Putaway'),
                        ('done', 'Done')
        ], 'State'),
	'purchase': fields.many2one('purchase.order', 'Purchase Order'),
	'lots': fields.one2many('stock.update.lots.from.receipt.wizard.lines', 'parent', string='Vendor Lots'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
	receipt_id = context.get('active_id')
	print 'RID', receipt_id
	receipt = self.pool.get('stock.vendor.receipt').browse(cr, uid, receipt_id)
	print 'RC', receipt
	items = []
	for item in receipt.license_plates:
	    items.append({'lot': item.id})

	res = {}
	res.update(lots=items)
	res.update({'receipt': context.get('active_id')})
        return res


    def mass_update_lots_from_receipt(self, cr, uid, ids, context=None):
	wizard = self.browse(cr, uid, ids[0])
	lot_obj = self.pool.get('stock.vendor.lot')
	lot_ids = []
	vals = {}

	for record in wizard.lots:
	    lot_ids.append(record.lot.id)

	if wizard.vendor:
	    vals.update({'vendor': wizard.vendor.id})

	if wizard.purchase:
	    vals.update({'purchase': wizard.purchase.id})

	if wizard.state:
	    vals.update({'state': wizard.state})

	lot_obj.write(cr, uid, lot_ids, vals)

	return True

	    
class StockUpdateLotsFromReceiptLinesWizard(osv.osv):
    _name = 'stock.update.lots.from.receipt.wizard.lines'
    _columns = {
	'parent': fields.many2one('stock.update.lots.from.receipt.wizard', 'Parent'),
	'lot': fields.many2one('stock.vendor.lot', string="License Plate"),
	'state': fields.related('lot', 'state', type="char", string='State'),
    }
