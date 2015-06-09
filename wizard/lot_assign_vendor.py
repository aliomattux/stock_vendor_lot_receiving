from openerp.osv import osv, fields
from openerp.tools.translate import _

class StockVendorLotAssignVendorWizard(osv.osv):
    _name = 'stock.vendor.lot.assign.vendor.wizard'
    _columns = {
	'name': fields.char('Name'),
	'vendor':fields.many2one('res.partner', 'Vendor'),
        'state': fields.selection([('draft', 'Draft'),
                        ('checkin', 'Pending Check-in'),
                        ('verification', 'Pending Verification'),
                        ('exception', 'Exception'),
                        ('putaway', 'Pending Putaway'),
                        ('done', 'Done')
        ], 'State'),
	'purchase': fields.many2one('purchase.order', 'Purchase Order'),
	'lots': fields.one2many('stock.vendor.lot.assign.vendor.wizard.lines', 'parent', string='Vendor Lots'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
	lots = context.get('active_ids')
	items = []
	for item in lots:
	    items.append({'lot': item})

	res = {}
	res.update(lots=items)
        return res


    def assign_lots_vendor(self, cr, uid, ids, context=None):
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

	    
class StockVendorLotAssignVendorLinesWizard(osv.osv):
    _name = 'stock.vendor.lot.assign.vendor.wizard.lines'
    _columns = {
	'parent': fields.many2one('stock.vendor.lot.assign.vendor.wizard', 'Parent'),
	'lot': fields.many2one('stock.vendor.lot', string="License Plate"),
	'state': fields.related('lot', 'state', type="char", string='State'),
    }
