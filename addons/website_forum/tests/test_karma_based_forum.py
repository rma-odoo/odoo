# -*- coding: utf-8 -*-
import openerp.tests

class Testkarma(openerp.tests.HttpCase):
    def test_karma(self):
        cr, uid = self.cr, self.uid
        # Usefull models
        forum_post = self.registry('forum.post');
        forum_tag = self.registry('forum.tag');
        forum_forum = self.registry('forum.forum');
        res_users = self.registry('res.users');
        res_partner = self.registry('res.partner');
        forum_help_ref = self.registry('ir.model.data').get_object_reference(cr, uid, 'website_forum', 'forum_help')[1]
        post_reason_ref = self.registry('ir.model.data').get_object_reference(cr, uid, 'website_forum', 'reason_1')[1]

        usera_ref =  res_users.create(cr, uid, {
            'name': 'Usera',
            'login': 'usera',
        })
        usera_ref_partner = res_users.browse(cr, uid, usera_ref).partner_id.id
        res_partner.write(cr, uid, usera_ref_partner, {'email': 'usera@gmail.com'})

        userb_ref =  res_users.create(cr, uid, {
            'name': 'Userb',
            'login': 'userb@gmail.com',
        })
        userb_ref_partner = res_users.browse(cr, uid, userb_ref).partner_id.id
        res_partner.write(cr, uid, userb_ref_partner, {'email': 'userb@gmail.com'})

        forum_forum_record = forum_forum.browse(cr, uid, uid)
        res_usera_record = res_users.browse(cr, uid, usera_ref)
        res_userb_record = res_users.browse(cr, uid, userb_ref)

        # Create 'Tags' 
        forum_tags_id = forum_tag.create(cr, uid, {
            'name': 'Contract',
            'forum_id': forum_help_ref,
        })

        # Post A user Questions
        usera_que_bef_karma = res_usera_record.karma
        usera_ques_id = forum_post.create(cr, usera_ref, {
            'name': 'What does XML-RPC be used in OpenERP ?',
            'forum_id': forum_help_ref,
            'views': 3,
            'tag_ids': [(4,forum_tags_id)],
        })
        res_usera_record.refresh()
        usera_que_aft_karma = res_usera_record.karma
        self.assertTrue((usera_que_aft_karma - usera_que_bef_karma) ==  forum_forum_record.karma_gen_question_new, "Karma earned for new questions not match.")

        # Post A user Answer
        usera_ans_id = forum_post.create(cr, usera_ref, {
            'forum_id': forum_help_ref,
            'content': """If you want do it via web service then have look at the OpenERP XML-RPC Web services. 
                        XML-RPC service can call function(CRUD as well as ORM), its arguments, and the result of the call are transported using HTTP and encoded using XML. 
                        XML-RPC can be used with Python, Java, Perl, PHP, C, C++, Ruby, Microsoft’s .NET and many other programming languages. Implementations are widely available for platforms such as Unix, Linux, Windows and the Macintosh.""",
            'parent_id': usera_ques_id,
        })

        # A upvote its question: not allowed
        usera_ques_create_uid = forum_post.browse(cr, usera_ref, usera_ques_id).create_uid.id
        self.assertTrue((usera_ques_create_uid == usera_ref),"A upvote its question not allowed.")

        #A upvote its answer: not allowed
        usera_ques_create_uid = forum_post.browse(cr, usera_ref, usera_ans_id).create_uid.id
        self.assertTrue((usera_ques_create_uid == usera_ref),"A upvote its answer not allowed.")

        #B comments A's question
        res_users.write(cr, uid, userb_ref,{'karma': forum_forum_record.karma_comment_own})
        self.assertTrue((res_userb_record.karma >= forum_forum_record.karma_comment_own) ,"User B karma is not enough comment A's question.")
        comment= """Access to OpenERP object methods (made available through XML-RPC from the server) is done via the openerp.web.Model() class. 
                This class maps onto the OpenERP server objects via two primary methods, call() and query()."""
        comment_id = forum_post.message_post(cr, userb_ref, usera_ques_id, comment, 'comment', subtype='mt_comment')

        #A converts the comment to an answer
        res_users.write(cr, uid, usera_ref,{'karma': forum_forum_record.karma_comment_convert_all})
        self.assertTrue((res_usera_record.karma >= forum_forum_record.karma_comment_convert_all) ,"A converts the comment to an answer is not enough karma")
        new_post_id = forum_post.convert_comment_to_answer(cr, usera_ref, comment_id)

        #A converts its answer to a comment
        forum_post.convert_answer_to_comment(cr, usera_ref, new_post_id)

        #Post B user Answer
        userb_ans_id = forum_post.create(cr, userb_ref, {
            'forum_id': forum_help_ref,
            'content': """As of today it you want to plan to integrate odoo apps with other 
                        application JSON is the correct approach as odoo is also support JSON API too. it is faster then the XML and you can do all when you can do with xml.""",
            'parent_id': usera_ques_id,
        })

        # User A upvote B's User answer
        res_users.write(cr, uid, usera_ref,{'karma': forum_forum_record.karma_gen_question_upvote})
        self.assertTrue((res_usera_record.karma >= forum_forum_record.karma_upvote) ,"User A karma is not enough upvote answer.")
        usera_upv_bef_karma = res_usera_record.karma
        userb_upv_bef_karma = res_userb_record.karma

        forum_post.vote(cr, usera_ref, [userb_ans_id], upvote=True)

        res_usera_record.refresh()
        res_userb_record.refresh()
        usera_upv_aft_karma = res_usera_record.karma
        userb_upv_aft_karma = res_userb_record.karma

        #check karma A user
        self.assertEqual(usera_upv_bef_karma, usera_upv_aft_karma, "karma update for a user is wrong.")
        #check karma B user
        self.assertTrue((userb_upv_aft_karma - userb_upv_bef_karma) ==  forum_forum_record.karma_gen_answer_upvote, "karma gen answer upvote not match.")

        #Post A accepts B's answer
        res_users.write(cr, uid, usera_ref,{'karma': forum_forum_record.karma_answer_accept_own})
        self.assertTrue((res_usera_record.karma >= forum_forum_record.karma_answer_accept_own) ,"User A karma is not enough accept answer.")
        usera_accept_bef_karma = res_usera_record.karma
        userb_accept_bef_karma = res_userb_record.karma

        post = forum_post.browse(cr, usera_ref, userb_ans_id)
        forum_post.write(cr, usera_ref, [post.id], {'is_correct': not post.is_correct})

        res_usera_record.refresh()
        res_userb_record.refresh()
        usera_accept_aft_karma = res_usera_record.karma
        userb_accept_aft_karma = res_userb_record.karma

        self.assertTrue((usera_accept_aft_karma - usera_accept_bef_karma) ==  forum_forum_record.karma_gen_answer_accept, "karma gen answer accept not match.")
        self.assertTrue((userb_accept_aft_karma - userb_accept_bef_karma) ==  forum_forum_record.karma_gen_answer_accepted, "karma gen answer accepted not match.")

        #User B down vote User A answer
        res_users.write(cr, uid, userb_ref,{'karma': forum_forum_record.karma_downvote})
        self.assertTrue((res_userb_record.karma >= forum_forum_record.karma_answer_accept_own) ,"User B karma is not enough accept answer.")
        usera_downv_bef_karma = res_usera_record.karma
        userb_downv_bef_karma = res_userb_record.karma

        forum_post.vote(cr, userb_ref, [usera_ans_id], upvote=False)

        res_usera_record.refresh()
        res_userb_record.refresh()
        usera_downv_aft_karma = res_usera_record.karma
        userb_downv_aft_karma = res_userb_record.karma
        self.assertTrue((usera_downv_aft_karma - usera_downv_bef_karma) ==  forum_forum_record.karma_gen_answer_downvote, "karma gen answer downvote not match.")
        self.assertEqual(userb_downv_bef_karma, userb_downv_aft_karma, "karma update for b user is wrong.")

        #A edits its own post
        res_users.write(cr, uid, usera_ref,{'karma': forum_forum_record.karma_edit_own})
        self.assertTrue((res_usera_record.karma >= forum_forum_record.karma_edit_own) ,"User A edit its own post karma is not enough.")
        vals={'content':"""If you want do it via web service then have look at the OpenERP XML-RPC Web services. 
                XML-RPC service can call function(CRUD as well as ORM), its arguments, and the result of the call are transported using HTTP and encoded using XML."""}
        forum_post.write(cr, usera_ref, [usera_ans_id], vals)

        # A edits B's post
        res_users.write(cr, uid, usera_ref,{'karma': forum_forum_record.karma_edit_all})
        self.assertTrue((res_usera_record.karma >= forum_forum_record.karma_edit_all) ,"User A edit B's post karma is not enough.")
        vals={'content': """As of today it you want to plan to integrate odoo apps with other 
                application JSON is the correct approach as odoo is also support JSON API too."""}
        forum_post.write(cr, usera_ref, [userb_ans_id], vals)

        #A closes its own post
        res_users.write(cr, uid, usera_ref,{'karma': forum_forum_record.karma_close_own})
        self.assertTrue((res_usera_record.karma >= forum_forum_record.karma_close_own) ,"A closes its own post karma is not enough.")
        forum_post.close(cr, usera_ref, [usera_ques_id], post_reason_ref)

        #A closes B's post
        # Post B user Questions
        userb_ques_id = forum_post.create(cr, userb_ref, {
            'name': 'How to give discount on the total of a Sales order ?',
            'forum_id': forum_help_ref,
            'views': 4,
            'tag_ids': [(4,forum_tags_id)],
        })

        res_users.write(cr, uid, usera_ref,{'karma': forum_forum_record.karma_close_all})
        self.assertTrue((res_usera_record.karma >= forum_forum_record.karma_close_all) ,"A closes b's post karma is not enough.")
        forum_post.close(cr, usera_ref, [userb_ques_id], post_reason_ref)

        #A delete its own post
        res_users.write(cr, uid, usera_ref,{'karma': forum_forum_record.karma_unlink_own})
        self.assertTrue((res_usera_record.karma >= forum_forum_record.karma_unlink_own) ,"A delete its own post karma is not enough.")
        forum_post.write(cr, usera_ref, [usera_ques_id], {'active': False})

        #A delete B's post
        res_users.write(cr, uid, usera_ref,{'karma': forum_forum_record.karma_unlink_all})
        self.assertTrue((res_usera_record.karma >= forum_forum_record.karma_unlink_all) ,"A delete b's post karma is not enough.")
        forum_post.write(cr, usera_ref, [userb_ques_id], {'active': False})
