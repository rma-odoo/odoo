(function(){
    "use strict";

    //for some pages required toggling
    $('#standard_div').css({"cursor": "pointer"}).click(function(ev) {
        $('#standard_div span').toggle();
        $('#fixed_span1').toggle();
    });
    $('#quote_div').css({"cursor": "pointer"}).click(function(ev) {
        $('#quote_div span').toggle();
        $('#fixed_span2').toggle();
    });
    $('#material_div').css({"cursor": "pointer"}).click(function(ev) {
        $('#material_div span').toggle();
        $('#contract_span2').toggle();
    });
    $('#subscription_div').css({"cursor": "pointer"}).click(function(ev) {
        $('#subscription_div span').toggle();
        $('#contract_span1').toggle();
    });
    $('#input_element_pipeline').change(function(ev) {
        var option = $(ev.target).find(":selected").val();
        if (option == 'solution_selling') {
            //fill pipeline stages
            $('#input_element_stage_1').val('Territory');
            $('#input_element_stage_2').val('Qualified');
            $('#input_element_stage_3').val('Qualified Sponsor');
            $('#input_element_stage_4').val('Proposal');
            $('#input_element_stage_5').val('Negotiation');
            $('#input_element_stage_6').val('Won');
            $('#input_element_stage_7').val('');
            //fill pipeline stage description
            $('#input_element_disc_1').val('New propspect assigned to the right salesperson');
            $('#input_element_disc_2').val('Set fields: Expected Revenue, Expected Closing Date, Next Action');
            $('#input_element_disc_3').val('You are in discussion with the decision maker and HE agreed on his pain points');
            $('#input_element_disc_4').val('Quotation sent to customer');
            $('#input_element_disc_5').val('The customer came back to you to discuss your quotation');
            $('#input_element_disc_6').val('Quotation signed by the customer');
            $('#input_element_disc_7').val('');

        }else if (option == 'b2c') {
            //fill pipeline stages
            $('#input_element_stage_1').val('New');
            $('#input_element_stage_2').val('Initial Contact');
            $('#input_element_stage_3').val('Product Demonstration');
            $('#input_element_stage_4').val('Proposal');
            $('#input_element_stage_5').val('Won');
            $('#input_element_stage_6').val('');
            $('#input_element_stage_7').val('');
            //fill pipeline stage description
            $('#input_element_disc_1').val('');
            $('#input_element_disc_2').val('Phone call with following questions: ...');
            $('#input_element_disc_3').val('Meeting with a demo. Set Fields: expected revenue, closing date');
            $('#input_element_disc_4').val('Quotation sent');
            $('#input_element_disc_5').val('');
            $('#input_element_disc_6').val('');
            $('#input_element_disc_7').val('');
        }else if (option == 'b2b') {
            //fill pipeline stages
            $('#input_element_stage_1').val('New');
            $('#input_element_stage_2').val('Qualified');
            $('#input_element_stage_3').val('Needs assessment');
            $('#input_element_stage_4').val('POC Sold');
            $('#input_element_stage_5').val('Demonstration');
            $('#input_element_stage_6').val('Proposal');
            $('#input_element_stage_7').val('Won');
            //fill pipeline stage description
            $('#input_element_disc_1').val('Set fields: Expected Revenue, Expected Closing Date, Next Action');
            $('#input_element_disc_2').val('Close opportunity if: "pre-sales days * $500" < "expected revenue" * probability');
            $('#input_element_disc_3').val('GAP analysis with customer');
            $('#input_element_disc_4').val('Create a Proof of Concept with consultants');
            $('#input_element_disc_5').val('POC demonstration to the customer');
            $('#input_element_disc_6').val('Final Proposal sent');
            $('#input_element_disc_7').val('');
        }else {
            //fill pipeline stages odoo default
            $('#input_element_stage_1').val('New');
            $('#input_element_stage_2').val('Qualified');
            $('#input_element_stage_3').val('Proposition');
            $('#input_element_stage_4').val('Negotiation');
            $('#input_element_stage_5').val('Won');
            $('#input_element_stage_6').val('Lost');
            $('#input_element_stage_7').val('');
            //fill pipeline stage description
            $("input[id^='input_element_disc']").val('');
        }
    });
    

})();
