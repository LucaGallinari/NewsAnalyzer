/**
 * Created by kalu on 03/04/15.
 *
 * Library of functions for handling filters management
 * with lots of transitions and some ajax request.
 *
 */
var addFilterForm     = "#addFilterForm";
var addFilterErrors   = "#addFilterErrors";
var modifyFilterForm  = "#modifyFilterForm";
var listFilters       = "#listFilters";

$(document).ready(function(){

    /* - ADD FILTER - */
    $(addFilterForm).on('submit', function() {
        // pre ajax request
        var buttonsRow = $(addFilterForm).find('.buttons-row').first();
        buttonsRow.find('button').hide();
        buttonsRow.append(preloader_wrapper('right'));

        // do an ajax req
        $.ajax({
            type: "POST",
            url: "/filters",
            data: $(this).serialize() // serializes the form's elements.
        })
        .done(function( data ) {
            data = data.toString();
            // rollback
            buttonsRow.find('.preloader-wrapper').remove();
            buttonsRow.find('button').show();

            if (data.indexOf("Ok")!=-1) { // if everything's ok
                Materialize.toast('Filter added!', 3000, 'rounded');
                var id = data.substr(4, data.length-4);
                addListElement(id);
                $(addFilterForm).trigger("reset");

                // hide no filter and errors
                if ($('.removeFilter').length==1) {
                    $(listFilters).removeClass('hide').show();
                    $('#noFilters').hide(500);
                }
                $(addFilterErrors).fadeOut();
            } else { // display error
                Materialize.toast('Ops! An error occured.', 3000, 'rounded');
                $(addFilterErrors).html(data).fadeIn();
            }
        })
        .fail(function () {
            // rollback
            buttonsRow.find('.preloader-wrapper').remove();
            buttonsRow.find('button').show();
            Materialize.toast('Ops! An error occured.', 3000, 'rounded');
        });
        return false; // avoid to execute the actual submit of the form.
    });


    /* - REMOVE FILTER - */
    $(listFilters).on('click', 'a.removeFilter', function() {
        // pre ajax request
        var id = $(this).attr('data-toggle');
        $('#agreeRemove').attr('data-toggle', id);
        $('#confirmModal').openModal();
    });

    $('.modal-footer').on('click', '#agreeRemove', function() {
        var id = $(this).attr('data-toggle');
        var parentId = "#removeFilter" + id;
        $(parentId).find('.removeFilter').hide();
        $(parentId).append(preloader_wrapper('center'));
        // do an ajax req
        $.ajax({
            type: "DELETE",
            url: '/filters?id='+id
        })
        .done(function( data ) {
            data = data.toString();
            if (data=="Ok") { // if everything's ok
                Materialize.toast('Filter removed!', 3000, 'rounded');
                $('#listFilter'+id).hide(500, function(){
                    // some animations
                    $(this).remove();
                    // show no filters panel
                    if ($('.removeFilter').length==0) {
                        $(listFilters).hide();
                        $('#noFilters').hide().removeClass('hide').show(500);
                    }
                });

            } else { // error
                // rollback
                $(parentId).find('.removeFilter').show();
                $(parentId).find('.preloader-wrapper').remove();
                // display error
                Materialize.toast('Ops! An error occured.', 3000, 'rounded');
                $(parentId).html(data);
            }
        })
        .fail(function () {
            // rollback
            $(parentId).find('.removeFilter').show();
            $(parentId).find('.preloader-wrapper').remove();
            // display error
            Materialize.toast('Ops! An error occured.', 3000, 'rounded');
        });
    });


    /* - MODIFY FILTER - */
    // set up
    $(addFilterForm).clone() // copy form for modifying
        .attr('id','modifyFilterForm') // modify id
        .appendTo('#modifyFilterContainer'); // append to modal
    $(modifyFilterForm).find('input').each(function(){ //change ids
        $(this).attr('id',$(this).attr('id')+'Modify')
    });
    $(modifyFilterForm).find('label').each(function(){ // change fors
        $(this).attr('for',$(this).attr('for')+'Modify')
    });

	$(modifyFilterForm).find('button').replaceWith(
    '<button class="btn waves-effect waves-orange right" type="submit" name="submit"> ' +
        'Save' +
    '</button>');

    // add close modal button
    $(modifyFilterForm).find('.buttons-row').append(
        '<button class="btn waves-effect waves-orange modal-close left red" type="button"> ' +
            'Close' +
        '</button>'
    );

    // events
    $(listFilters).on('click', 'a.modifyFilter', function() {
        // pre ajax request
        var id = $(this).attr('data-toggle');
        //$(this).hide();
        setupModifyForm(id);
        $('#modifyModal').openModal();
        $('#modifyFilterErrors').hide();
    });

    $(modifyFilterForm).on('submit', function() {
        // pre ajax request
        var buttonsRow = $(this).find('.buttons-row').first();
        var id = buttonsRow.find('button').attr('data-toggle');
        $('#modifyFilterErrors').hide();
        buttonsRow.find('button').hide();
        buttonsRow.append(preloader_wrapper('right'));
        // do an ajax req
        $.ajax({
            type: "PUT",
            url: '/filters?id='+id,
            data: $(this).serialize() // serializes the form's elements.
        })
        .done(function(data) {
            data = data.toString();
            //$('#modifyFilterErrors').html(data);
            buttonsRow.find('.preloader-wrapper').remove();
            buttonsRow.find('button').show();
            if (data.toString()=="Ok") { // if everything's ok
                Materialize.toast('Filter modified!', 3000, 'rounded');
                modifyListElement(id);
                $('#modifyModal').closeModal();
            } else { // if not display error
                Materialize.toast('Ops! An error occured.', 3000, 'rounded');
                $('#modifyFilterErrors').html(data).fadeIn().delay(3000).fadeOut();
            }
        })
        .fail(function () {
            // rollback
            buttonsRow.find('.preloader-wrapper').remove();
            buttonsRow.find('button').show();
            // display error
            Materialize.toast('Ops! An error occured.', 3000, 'rounded');
        });
        return false; // avoid to execute the actual submit of the form.
    });

});

function modifyListElement(id) {
    $(modifyFilterForm).find('input, select').each(function(){ // for each input fill the respective td
        var val = $(this).val();
        // -1 value = no
        if ($(this).attr('name')=="email_hour" && val=="-1")
            val = "no";
        $('#listFilter'+id) // get the tr
            .find('.'+$(this).attr('name')) // get the respective "td"
            .html(val);// set the value of that element
    });
}

function setupModifyForm(id) {
    $(modifyFilterForm).find('input, select').each(function(){ // fill each input with respective value
        var val = $('#listFilter'+id) // get the tr
            .find('.'+$(this).attr('name')) // get the respective "td"
            .html(); // get the value of that element
        // -1 value = no
        if ($(this).attr('name')=="email_hour" && val=="no")
            val = "-1";
        $(this).val(val).focusin();
    });
    $(modifyFilterForm).find('select').material_select();
    $(modifyFilterForm).find('button').attr('data-toggle', id);
}

function addListElement(id) {
    // get values
    var name = $(addFilterForm).find('input[name="name"]').first().val();
    var keyw = $(addFilterForm).find('input[name="keywords"]').first().val();
    var email = $(addFilterForm).find('select[name="email_hour"]').first().val();

    // add element
    var el = $(list_element(id, name, keyw, email));
    el.hide();
    $(listFilters).find('tbody').append(el);
    $('.dropdown-button').dropdown();

    el.fadeIn();
}

function list_element(id, name, keyw, email) {
    return ' \
        <tr id="listFilter'+(id)+'" class="new collection-item"> \
            <td class="name">'+name+'</td> \
            <td class="keywords">'+keyw+'</td> \
            <td class="email_hour">'+((email=="-1") ? "no" : email)+'</td> \
            <td class="modify"><a data-toggle="'+(id)+'" class="modifyFilter">Edit</a></td> \
            <td class="remove"><a data-toggle="'+(id)+'" class="removeFilter">Remove</a></td> \
        </tr>';


}

function preloader_wrapper(pos) {
    return ' \
        <div class="preloader-wrapper small active '+pos+'"> \
            <div class="spinner-layer spinner-green-only"> \
                <div class="circle-clipper left"> \
                <div class="circle"></div> \
                </div><div class="gap-patch"> \
                <div class="circle"></div> \
                </div><div class="circle-clipper right"> \
                <div class="circle"></div> \
                </div> \
            </div> \
        </div>';
}
