function open_share_dialog(social_network) {
    var url = location.origin + location.pathname
    if ($("#question_name_ask").length === 0) {
        var text_to_share = "Just answered #odoo question " + url + " " + $("#question_name").text()
    } else {
        url = location.origin + $("#share_dialog_box").data("url");
        var text_to_share = $("#question_name_ask").val() + " #odoo #help " + url
    }
    if (social_network == 'twitter') {
        var sharing_url = 'https://twitter.com/intent/tweet?original_referer=' + encodeURIComponent(url) + '&amp;text=' + encodeURIComponent(text_to_share);
        $("#share_dialog_box").data("twitter", true);
    } else if (social_network == 'linked-in') {
        var sharing_url = 'https://www.linkedin.com/shareArticle?mini=true&amp;url=' + encodeURIComponent(url) + '&amp;title=' + encodeURIComponent(text_to_share) + '&amp;summary=Odoo Forum&amp;source=Odoo forum';
        $("#share_dialog_box").data("linked_in", true);
    } else {
        var sharing_url = 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url);
        $("#share_dialog_box").data("facebook" , true);
    }
    window.open(sharing_url, '', 'menubar=no, toolbar=no, resizable=yes, scrollbar=yes, height=600,width=600');
    return false;
}

function decode_like_post(values_serialize) {
    decode_values = {};
    for (value in values_serialize) {
        decode_values[values_serialize[value]['name']] = values_serialize[value]['value'];
    }
    return decode_values;
}

function redirect_user ($form) {
    var path = $form.data("target");
    openerp.jsonRpc(path,  "call", decode_like_post($form.serializeArray()))
        .then(function(result) {
            $(".modal-title").text(result['title']);
            $(".modal-body").prepend(result['body']);
            $("#share_dialog_box").data({
                "id" : result['question_id'],
                "twitter" : false,
                "facebook" : false,
                "linked_in" : false,
                "url" : result['redirect_url'],
            }).on('hidden.bs.modal', function() {
                var vals = [parseInt($("#share_dialog_box").data('id'))]
                vals.push ({
                    'on_twitter' : $(this).data("twitter"),
                    'on_facebook' : $(this).data("facebook"),
                    'on_linked_in' : $(this).data("linked_in"),
                });
                var Post = openerp.website.session.model('forum.post')
                Post.call('write', vals).then(function(data) {
                    window.location = result['redirect_url'];
                });
            }).modal("show"); });
}

$(document).ready(function () {

    $(".tag_text").submit(function(event) {
        event.preventDefault();
        CKEDITOR.instances['content'].destroy();
        redirect_user($(this));
    });

    $("#forum_post_answer").submit(function(event) {
        event.preventDefault();
        CKEDITOR.instances['content'].destroy();
        redirect_user($(this));
    });

    $('.karma_required').on('click', function (ev) {
        var karma = $(ev.currentTarget).data('karma');
        if (karma) {
            ev.preventDefault();
            var $warning = $('<div class="alert alert-danger alert-dismissable oe_forum_alert" id="karma_alert">'+
                '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                karma + ' karma is required to perform this action. You can earn karma by answering questions or having '+
                'your answers upvoted by the community.</div>');
            var vote_alert = $(ev.currentTarget).parent().find("#vote_alert");
            if (vote_alert.length == 0) {
                $(ev.currentTarget).parent().append($warning);
            }
        }
    });

    $('.vote_up,.vote_down').not('.karma_required').on('click', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        openerp.jsonRpc($link.data('href'), 'call', {})
            .then(function (data) {
                if (data['error']){
                    if (data['error'] == 'own_post'){
                        var $warning = $('<div class="alert alert-danger alert-dismissable oe_forum_alert" id="vote_alert">'+
                            '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                            'Sorry, you cannot vote for your own posts'+
                            '</div>');
                    } else if (data['error'] == 'anonymous_user'){
                        var $warning = $('<div class="alert alert-danger alert-dismissable oe_forum_alert" id="vote_alert">'+
                            '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                            'Sorry you must be logged to vote'+
                            '</div>');
                    }
                    vote_alert = $link.parent().find("#vote_alert");
                    if (vote_alert.length == 0) {
                        $link.parent().append($warning);
                    }
                } else {
                    $link.parent().find("#vote_count").html(data['vote_count']);
                    if (data['user_vote'] == 0) {
                        $link.parent().find(".text-success").removeClass("text-success");
                        $link.parent().find(".text-warning").removeClass("text-warning");
                    } else {
                        if (data['user_vote'] == 1) {
                            $link.addClass("text-success");
                        } else {
                            $link.addClass("text-warning");
                        }
                    }
                }
            });
        return true;
    });

    $('.accept_answer').not('.karma_required').on('click', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        openerp.jsonRpc($link.data('href'), 'call', {}).then(function (data) {
            if (data['error']) {
                if (data['error'] == 'anonymous_user') {
                    var $warning = $('<div class="alert alert-danger alert-dismissable" id="correct_answer_alert" style="position:absolute; margin-top: -30px; margin-left: 90px;">'+
                        '<button type="button" class="close notification_close" data-dismiss="alert" aria-hidden="true">&times;</button>'+
                        'Sorry, anonymous users cannot choose correct answer.'+
                        '</div>');
                }
                correct_answer_alert = $link.parent().find("#correct_answer_alert");
                if (correct_answer_alert.length == 0) {
                    $link.parent().append($warning);
                }
            } else {
                if (data) {
                    $link.addClass("oe_answer_true").removeClass('oe_answer_false');
                } else {
                    $link.removeClass("oe_answer_true").addClass('oe_answer_false');
                }
            }
        });
        return true;
    });

    $('.favourite_question').on('click', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        openerp.jsonRpc($link.data('href'), 'call', {}).then(function (data) {
            if (data) {
                $link.addClass("forum_favourite_question")
            } else {
                $link.removeClass("forum_favourite_question")
            }
        });
        return true;
    });

    $('.comment_delete').on('click', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        openerp.jsonRpc($link.data('href'), 'call', {}).then(function (data) {
            $link.parents('.comment').first().remove();
        });
        return true;
    });

    $('.notification_close').on('click', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        openerp.jsonRpc("/forum/notification_read", 'call', {
            'notification_id': $link.attr("id")})
        return true;
    });

    if($('input.load_tags').length){
        var tags = $("input.load_tags").val();
        $("input.load_tags").val("");
        set_tags(tags);
    };

    function set_tags(tags) {
        $("input.load_tags").textext({
            plugins: 'tags focus autocomplete ajax',
            tagsItems: tags.split(","),
            //Note: The following list of keyboard keys is added. All entries are default except {32 : 'whitespace!'}.
            keys: {8: 'backspace', 9: 'tab', 13: 'enter!', 27: 'escape!', 37: 'left', 38: 'up!', 39: 'right',
                40: 'down!', 46: 'delete', 108: 'numpadEnter', 32: 'whitespace!'},
            ajax: {
                url: '/forum/get_tags',
                dataType: 'json',
                cacheResults: true
            }
        });
        // Adds: create tags on space + blur
        $("input.load_tags").on('whitespaceKeyDown blur', function () {
            $(this).textext()[0].tags().addTags([ $(this).val() ]);
            $(this).val("");
        });
        $("input.load_tags").on('isTagAllowed', function(e, data) {
            if (_.indexOf($(this).textext()[0].tags()._formData, data.tag) != -1) {
                data.result = false;
            }
        });
    }

    if ($('textarea.load_editor').length) {
        var editor = CKEDITOR.instances['content'];
        editor.on('instanceReady', CKEDITORLoadComplete);
    }
});

function IsKarmaValid(eventNumber,minKarma){
    "use strict";
    if(parseInt($("#karma").val()) >= minKarma){
        CKEDITOR.tools.callFunction(eventNumber,this);
        return false;
    } else {
        alert("Sorry you need more than " + minKarma + " Karma.");
    }
}

function CKEDITORLoadComplete(){
    "use strict";
    $('.cke_button__link').attr('onclick','IsKarmaValid(33,30)');
    $('.cke_button__unlink').attr('onclick','IsKarmaValid(37,30)');
    $('.cke_button__image').attr('onclick','IsKarmaValid(41,30)');
}
