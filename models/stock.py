from openerp.osv import osv, fields


class StockMove(osv.osv):
    _inherit = 'stock.move'
    _columns = {
	'stock.vendor.lot.line': fields.many2one('stock.vendor.lot.line', 'Vendor Receipt Line'),
    }
