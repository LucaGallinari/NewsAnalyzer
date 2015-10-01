/**
 * Created by kalu on 29/09/15.
 *
 * Library of functions for handling favorites management
 * with lots of transitions and some ajax request.
 *
 */
    /* JQuery objs */
    var $newsWall = $('#newsWall');

$(document).ready(function(){

    /* - REMOVE FAVORITE - */
    $newsWall.on('click', 'a.remfav', function() {
        // pre ajax request
        var id = $(this).attr('data-toggle');
        $('#agreeRemove').attr('data-toggle', id);
        $('#confirmModal').openModal();
    });

    $('.modal-footer').on('click', '#agreeRemove', function() {
        var id = $(this).attr('data-toggle');
        // do an ajax req
        $.ajax({
            type: "DELETE",
            url: '/favorites?id='+id
        })
        .done(function( data ) {
            data = data.toString();
            if (data=="Ok") { // if everything's ok
                Materialize.toast('Favorite removed!', 3000, 'rounded');
                // var $obj = $newsWall.find('a[data-toggle="'+id+'"]');
                $('#fav-'+id).fadeOut(500, function(){
                    $(this).remove();
                });
            } else { // error
                Materialize.toast('Ops! An error occured.', 3000, 'rounded');
                Materialize.toast(data, 3000, 'rounded');
            }
        })
        .fail(function () {
            Materialize.toast('Ops! An error occured.', 3000, 'rounded');
        });
    });

});

