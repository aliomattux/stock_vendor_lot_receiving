from openerp.osv import osv, fields
from openerp.tools.translate import _

class StockVendorLotWizard(osv.osv):
    _name = 'stock.vendor.lot.wizard'
    _rec_name = 'license_plate'
    _columns = {
        'license_plate': fields.char('License Plate'),
	'vendor':fields.many2one('res.partner', 'Vendor'),
	'vendor_lot': fields.many2one('stock.vendor.lot', 'License Plate'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
	print 'Function Call', context
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
		'vendor': context.get('default_vendor'),
		'vendor_lot': context.get('default_vendor_lot'),
	    }

	return res

    def create_new_licenseplate(self, cr, uid, wizard):
	lot_obj = self.pool.get('stock.vendor.lot')
	if wizard:
	    vals = {
		    'vendor': wizard.vendor.id,
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
	print 'AFTER'
	wizard = self.browse(cr, uid, ids[0])
	lot = self.create_new_licenseplate(cr, uid, wizard)
	context.update({'default_vendor_lot': lot.id,
			'default_license_plate': lot.license_plate,
			'default_vendor': wizard.vendor.id,
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
