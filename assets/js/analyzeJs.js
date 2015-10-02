/**
 * Created by kalu on 01/10/15.
 *
 */

var $entity = $('.entity');
var num_per_page = 5;
var page = 1;

$(document).ready(function(){

    /* Events */
    $entity.on('click', '.collapsible-header', function() {

        var index = $(this).attr('data-index');
        var label = $(this).attr('data-label');
        var loaded = $(this).attr('data-loaded');
        var $load = $('#loading-'+index);
        if (!(loaded===undefined)) { // images already loaded
            console.log(1);
            return;
        }
        $(this).attr('data-loaded','1');
        Materialize.toast('Loading images for '+label, 2000);
        $load.show();
        loadImages($load, label);
    });

    $entity.on('click', '.more-images', function() {

        var index = $(this).attr('data-index');
        var label = $(this).attr('data-label');
        var $load = $('#loading-'+index);

        Materialize.toast('Loading images for '+label, 2000);
        $load.show();
        loadImages($load, label);
        return false;
    });

});

function loadImages($load, label) {
    $.ajax({
        type: "GET",
        url: "/api/flickr",
        data:  {
            label: label,
            page: page,
            per_page: num_per_page
        }
    })
    .done(function (data) {
        var obj = JSON.parse(data);
        if (obj.length == 0) {
            Materialize.toast('No images found!', 4000);
            // TODO: no image panel
            return;
        }
        // loop images
        if (!('photos' in obj)) {
            // no photos
            return;
        }
        if (!('photo' in obj.photos)) {
            // no photos
            return;
        }
        var arr = obj.photos.photo;
        var $imgs = $load.parent();
        $load.hide();
        for (var i in arr) {
            if (arr.hasOwnProperty(i)) {
                var img = arr[i];
                addImage($imgs, img);
            }
        }
        $('.materialboxed').materialbox();
        ++page;
    })
    .fail(function () {
        Materialize.toast('Error while retrieving info from the server', 4000);
        $load.hide();
    })
}

function addImage($imgs, img) {
    var htmlEl =
        '<div class="img col">  \
            <img class="materialboxed" data-caption="'+ img.title +'" \
                src="https://farm'+ img.farm +'.staticflickr.com/'+ img.server +'/'+ img.id +'_'+ img.secret +'.jpg" \
                title="" \
                alt="'+ img.title +'"> \
        </div>';
    $(htmlEl).hide().appendTo($imgs).fadeIn(1000);
}