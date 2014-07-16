$(document).ready(function () {
    $('#attendeeform .a-submit')
        .off('click')
        .removeClass('a-submit')
        .click(function (event) {
            event.preventDefault();
            var $form = $(this).closest('form');
            var name_and_quantity = {};
            $("select").each(function() {
                name_and_quantity[$(this)[0].name] = $(this).val();
            });
            openerp.jsonRpc("/event/generate/attendeeform", 'call', {
                'event_id': parseInt(this.id),
                post: name_and_quantity,
            }).then(function (modal) {
                var $modal = $(modal);
                var attendee_form = $('#attendee_registration');
                $modal.appendTo($form)
                    .modal()
                    .on('hidden.bs.modal', function () {
                        $(this).remove();
                    });
                $modal.on('click', '.a-submit', function () {
                    attendee_form.on('submit', function(e){
                        e.preventDefault();
                        $.ajax({
                            url: attendee_form.attr('action'),
                            type: attendee_form.attr('method'),
                            data: attendee_form.serialize(),
                        });
                    });
                });
                $modal.on('click', '.js_goto_event', function () {
                    $modal.modal('hide');
                });
            });
        });
});
