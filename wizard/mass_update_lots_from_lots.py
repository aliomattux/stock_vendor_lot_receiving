from openerp.osv import osv, fields
from openerp.tools.translate import _

class StockUpdateLotsFromLotsWizard(osv.osv_memory):
    _name = 'stock.update.lots.from.lots.wizard'
    _columns = {
	'name': fields.char('Name'),
	'vendor':fields.many2one('res.partner', 'Vendor'),
        'state': fields.selection([('draft', 'Draft'),
                        ('checkin', 'Ready to Count'),
                        ('verification', 'Pending Verification'),
                        ('exception', 'Exception'),
                        ('putaway', 'Pending Putaway'),
                        ('done', 'Done')
        ], 'State'),
        'purchases': fields.many2many('purchase.order', \
                'mass_update_from_lots_wizard_purchase_rel', 'lot_id', 'purchase_id',
		string='Purchase Orders', domain="[('partner_id', '=', vendor)]"
        ),
	'lots': fields.one2many('stock.update.lots.from.lots.wizard.lines', 'parent', string='Vendor Lots'),
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


    def mass_update_lots_from_lots(self, cr, uid, ids, context=None):
	wizard = self.browse(cr, uid, ids[0])
	lot_obj = self.pool.get('stock.vendor.lot')
	lot_ids = []
	vals = {}

	for record in wizard.lots:
	    lot_ids.append(record.lot.id)

	if wizard.vendor:
	    vals.update({'vendor': wizard.vendor.id})

	if wizard.purchases:
	    purchase_ids = [purch.id for purch in wizard.purchases]
	    vals.update({'purchases': [(6, 0, purchase_ids)]})

	if wizard.state:
	    vals.update({'state': wizard.state})

	lot_obj.write(cr, uid, lot_ids, vals)

	return True

	    
class StockUpdateLotsFromLotsLinesWizard(osv.osv_memory):
    _name = 'stock.update.lots.from.lots.wizard.lines'
    _columns = {
	'parent': fields.many2one('stock.update.lots.from.lots.wizard', 'Parent'),
	'lot': fields.many2one('stock.vendor.lot', string="License Plate"),
	'state': fields.related('lot', 'state', type="char", string='State'),
    }
