from openerp.osv import osv, fields
from datetime import datetime

class StockVendorReceipt(osv.osv):
    _name = 'stock.vendor.receipt'
    _columns = {
	'name': fields.char('Name'),
	'license_plates': fields.one2many('stock.vendor.lot', 'receipt', string="License Plates"),
	'start_time': fields.datetime('Start Time'),
	'end_time': fields.datetime('End Time'),
	'purchase': fields.many2one('purchase.order', 'Purchase'),
	'vendor':fields.many2one('res.partner', 'Vendor'),
    }

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'stock.vendor.receipt') or '/'

	if not context.get('start_time'):
	    vals['start_time'] = datetime.utcnow()
	
        return super(StockVendorReceipt, self).create(cr, uid, vals, context)


class StockVendorLot(osv.osv):
    _name = 'stock.vendor.lot'
    _rec_name = 'license_plate'
    _columns = {
	'receipt': fields.many2one('stock.vendor.receipt', 'Vendor Receipt'),
	'license_plate': fields.char('License Plate'),
        'vendor':fields.many2one('res.partner', 'Vendor'),
	'state': fields.selection([('draft', 'Draft'),
			('checkin', 'Ready to Count'),
			('verification', 'Pending Verification'),
			('exception', 'Exception'),
			('putaway', 'Pending Putaway'),
			('done', 'Done')
	], 'State'),
	'purchase': fields.many2one('purchase.order', 'Purchase'),
	'lot_items': fields.one2many('stock.vendor.lot.line', 'vendor_lot', string="Lot Items"),
    }

    _defaults = {
	'state': 'draft',
    }


    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if ('license_plate' not in vals) or (vals.get('license_plate') in ('/', False)):
	    vals['license_plate'] = self.pool.get('ir.sequence').get(cr, uid, 'stock.vendor.lot') or '/'

        return super(StockVendorLot, self).create(cr, uid, vals, context)




class StockVendorLotItem(osv.osv):
    _name = 'stock.vendor.lot.line'
    _columns = {
	'name': fields.char('Name'),
	'vendor_lot': fields.many2one('stock.vendor.lot', 'Vendor Lot'),
	'product_qty': fields.float('Quantity'),
	'product': fields.many2one('product.product', 'Product'),
    }
