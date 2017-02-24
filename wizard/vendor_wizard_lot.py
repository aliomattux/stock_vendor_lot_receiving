from openerp.osv import osv, fields
from openerp.tools.translate import _

class StockVendorLotWizard(osv.osv_memory):
    _name = 'stock.vendor.lot.wizard'
    _rec_name = 'license_plate'
    _columns = {
	'receipt': fields.many2one('stock.vendor.receipt', 'Receipt'),
        'license_plate': fields.char('License Plate'),
	'vendor':fields.many2one('res.partner', 'Vendor'),
        'purchases': fields.many2many('purchase.order', \
                'vendor_create_lots_wizard_purchase_rel', 'wizard_id', 'purchase_id',
		string='Purchase Orders', domain="[('partner_id', '=', vendor)]"
        ),
	'vendor_lot': fields.many2one('stock.vendor.lot', 'License Plate'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
	#There is some bug where the wizard default get is called multiple times
	#context is immutable so we will check if this is the only field then we
	#know its a bogus call and immediately return
	if fields == ['vendor_lot']:
	    print 'returning'
	    return {}

	if not context.get('repeatable'):
	    lot = self.create_new_licenseplate(cr, uid, wizard=False)
            res = {'license_plate': lot.license_plate,
		   'vendor_lot': lot.id,
		   'vendor': context.get('vendor'),
            }
            return res

	else:
	    res = {
		'license_plate': context.get('default_license_plate'),
		'receipt': context.get('default_receipt'),
		'vendor': context.get('default_vendor'),
		'purchases': context.get('default_purchases'),
		'vendor_lot': context.get('default_vendor_lot'),
	    }

	return res


    def create_new_licenseplate(self, cr, uid, wizard):
	lot_obj = self.pool.get('stock.vendor.lot')
	if wizard:
	    if wizard.purchases:
		purchase_ids = [purch.id for purch in wizard.purchases]
	    else:
		purchases = []
	    vals = {
		    'vendor': wizard.vendor.id,
		    'receipt': wizard.receipt.id,
		    'purchases': [(6, 0, purchase_ids)],
	    }

	else:
	    vals = {}

	lot_id = lot_obj.create(cr, uid, vals)
	return lot_obj.browse(cr, uid, lot_id)


    def print_license_plate(self, cr, uid, ids, context=None):
        return True



    def create_vendor_lot(self, cr, uid, ids, context=None):
	return True


    def create_vendor_lot_and_continue(self, cr, uid, ids, context=None):
	wizard = self.browse(cr, uid, ids[0])
	if not context.get('repeatable'):
	    first_lot = wizard.vendor_lot
	    first_lot.receipt = wizard.receipt.id

	lot = self.create_new_licenseplate(cr, uid, wizard)
	context.update({'default_vendor_lot': lot.id,
			'default_receipt': wizard.receipt.id,
			'default_license_plate': lot.license_plate,
			'default_vendor': wizard.vendor.id,
			'default_purchases': [purch.id for purch in wizard.purchases],
			'repeatable': True,
	})
        return {
            'name':_("Create License Plate"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'stock.vendor.lot.wizard',
            'type': 'ir.actions.act_window',
#            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }
