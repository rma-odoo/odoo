$(document).ready(function () {
<<<<<<< HEAD
<<<<<<< HEAD

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
    $('.collapse a').hover( function() {
        console.log("I am on the button");
        $(this).animate({fontSize: '2em' }, "fast");
    },
      function() {
        console.log("I am out of the button");
        $(this).animate({fontSize: '1.333em' }, "fast");
      });
=======
=======

    $(":not(li .share_link)").click(function (e) {
        $("li .share_link").popover("hide");
        e.stopPropagation();
    });

    $("li .share_link").click(function (e) {
        e.stopPropagation();
    });

<<<<<<< HEAD
    $(location.hash).bind("transitionend webkitTransitionEnd oTransitionEnd MSTransitionEnd", function() {
        $(this).css("background-color", "white");
    }).css("background-color", '#82889E');

>>>>>>> 25b6112... [FIX,ADD] website_forum: Fixed the issue of URL when user shares post which is alredy shared. Added flash feature when the URL is open with hash(#) in URL
    $("li .share_link").each(function(index) {
=======
    var transition_value = "background-color 1s";
    /*JSH Note: It is required to set transition propery because of Jquery issue #14836 for Chrome*/
    $(location.hash).css({"-webkit-transition" : transition_value, "-moz-transition" : transition_value, "transition" : transition_value, "-o-transition" : transition_value});
    $(location.hash).one("webkitTransitionEnd transitionend oTransitionEnd MSTransitionEnd", function() {
        $(this).removeClass("label-primary");
    }).addClass("label-primary");
 
    $("li .share_link").each(function() {
>>>>>>> b436f98... [FIX] website_forum: The issue of Chrome of blincking feature for highliting user shared answer
        var target = $(this).data('target');
        $(this).popover({
            html : true,
            content : function() {
                return $(target).html();
            }
        });
    });
<<<<<<< HEAD
>>>>>>> 801606e... [IMP] View: Converted the sharing buttons in bootstrap popover.
=======

>>>>>>> 25b6112... [FIX,ADD] website_forum: Fixed the issue of URL when user shares post which is alredy shared. Added flash feature when the URL is open with hash(#) in URL
    $('.vote_up ,.vote_down').on('click', function (ev) {
>>>>>>> d885757... [ADD] open graph meta description tag for facebook.
=======
    ('.vote_up ,.vote_down').on('click', function (ev) {
>>>>>>> 9fcf9e3... [IMP] Sharing functionality with schema description
=======
    $('.vote_up ,.vote_down').on('click', function (ev) {
>>>>>>> 6b8d06c... [IMP] Added OpenGraph tags for Facebook and Schema tag for Google Plus
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
