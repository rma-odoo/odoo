from openerp.osv import fields,osv
from openerp import tools


class im_livechat_report(osv.Model):
    """ Livechat Support Report """
    _name = "im_livechat.report"
    _auto = False
    _description = "Livechat Support Report"
    _columns = {
        'uuid': fields.char('UUID', size=50, readonly=True),
        'start_date': fields.datetime('Start Date of session', readonly=True),
        'start_date_hour': fields.datetime('Hour of start Date of session', readonly=True),
        'duration': fields.float('Average duration', digits=(16,2), readonly=True, group_operator="avg"),
        'time_in_session': fields.float('Time in session', digits=(16,2), readonly=True, group_operator="avg"),
        'time_to_answer': fields.float('Time to answer', digits=(16,2), readonly=True, group_operator="avg"),
        'nbr_messages': fields.integer('Average message', readonly=True, group_operator="avg"),
        'nbr_user_messages': fields.integer('Average of messages/user', readonly=True, group_operator="avg"),
        'nbr_speakers': fields.integer('# of speakers', readonly=True, group_operator="avg"),
        'rating': fields.float('Average rating', readonly=True, group_operator="avg"),
        'user_id': fields.many2one('res.users', 'User', readonly=True),
        'session_id': fields.many2one('im_chat.session', 'Session', readonly=True),
        'channel_id': fields.many2one('im_livechat.channel', 'Channel', readonly=True),
    }
    _order = 'start_date, uuid'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'im_livechat_report')
        cr.execute("""
            CREATE OR REPLACE VIEW im_livechat_report AS (
                SELECT
                    min(M.id) as id,
                    S.uuid as uuid,
                    S.create_date as start_date,
                    date_trunc('hour', S.create_date) as start_date_hour,
                    EXTRACT('epoch' from ((SELECT (max(create_date)-min(create_date)) FROM im_chat_message WHERE to_id=S.id AND from_id = U.id))) as time_in_session,
                    EXTRACT('epoch' from ((SELECT min(create_date) FROM im_chat_message WHERE to_id=S.id AND from_id IS NOT NULL)-(SELECT min(create_date) FROM im_chat_message WHERE to_id=S.id AND from_id IS NULL))) as time_to_answer,
                    EXTRACT('epoch' from (max((SELECT (max(create_date)) FROM im_chat_message WHERE to_id=S.id))-S.create_date)) as duration,
                    (SELECT count(distinct COALESCE(from_id, 0)) FROM im_chat_message WHERE to_id=S.id) as nbr_speakers,
                    (SELECT count(id) FROM im_chat_message WHERE to_id=S.id) as nbr_messages,
                    count(M.id) as nbr_user_messages,
                    CAST(S.feedback_rating AS INT) as rating,
                    U.id as user_id,
                    S.channel_id as channel_id
                FROM im_chat_message M
                    LEFT JOIN im_chat_session S on (S.id = M.to_id)
                    LEFT JOIN res_users U on (U.id = M.from_id)
                WHERE S.channel_id IS NOT NULL
                GROUP BY U.id, M.to_id, S.id
            )
        """)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
