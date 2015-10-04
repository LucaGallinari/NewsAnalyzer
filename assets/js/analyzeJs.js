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
        var categ = $(this).attr('data-categ');
        var $loadImg = $('#loading_images-'+index);
        var $loadVid = $('#loading_videos-'+index);
        if (!($(this).attr('data-loaded')===undefined)) { // data already loaded
            return;
        }
        $(this).attr('data-loaded','1');

        // images
        Materialize.toast('Loading images for '+label, 2000);
        $loadImg.show();
        loadImages($loadImg, label);

        // videos
        if (categ=='event' || categ=='film') {
            Materialize.toast('Loading videos for '+label, 2000);
            $loadVid.show();
            loadVideos($loadVid, label);
        }
    });

    $entity.on('click', '.more-images', function() {

        var index = $(this).attr('data-index');
        var label = $(this).attr('data-label');
        var $load = $('#loading_images-'+index);

        Materialize.toast('Loading images for '+label, 2000);
        $load.show();
        loadImages($load, label);
        return false;
    });

    /* Dynamically load youtube videos by showing a preview image and
     * only on click it will load the embedded video.
     * CREDITS: http://www.labnol.org/internet/light-youtube-embeds/27941/
    */
    $('.youtube-container').on('click', '.youtube-player > div', function() {
        var id = $(this).parent().attr('data-id');
        if (id===undefined) {
            return false;
        }
        var $iframe = $('<iframe></iframe>');
        $iframe.attr(
            'src',
            '//www.youtube.com/embed/'+id+
            '?autoplay=1&autohide=2&border=0&wmode=opaque&enablejsapi=1&controls=1&showinfo=0&iv_load_policy=3'
        );
        $iframe.attr("frameborder", "0");
        $iframe.attr("id", "youtube-iframe");
        $iframe.attr("allowfullscreen", "");
        $(this).replaceWith($iframe);
        //.parent().replaceChild($iframe, this);
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
        Materialize.toast('Error while retrieving images from the server', 4000);
        $load.hide();
    })
}

function loadVideos($load, search) {
    $.ajax({
        type: "GET",
        url: "/api/youtube",
        data:  {search: search}
    })
    .done(function (data) {
        var arr = JSON.parse(data);
        if (arr.length == 0) {
            Materialize.toast('No videos found!', 4000);
            // TODO: no video panel
            return;
        }
        var $vids = $load.parent();
        $load.hide();
        for (var i in arr) {
            if (arr.hasOwnProperty(i)) {
                var vid = arr[i];
                addVideo($vids, vid);
            }
        }
    })
    .fail(function () {
        Materialize.toast('Error while retrieving videos from the server', 4000);
        $load.hide();
    })
}

function addImage($imgs, img) {
    var htmlEl =
        '<div class="img col">  \
            <img \
                class="materialboxed" data-caption="'+ img.title +'" \
                src="https://farm'+ img.farm +'.staticflickr.com/'+ img.server +'/'+ img.id +'_'+ img.secret +'.jpg" \
                title="" \
                alt="'+ img.title +'"> \
        </div>';
    $(htmlEl).hide().appendTo($imgs).fadeIn(1000);
}

function addVideo($vids, vid) {
    var htmlEl =
        '<div class="youtube-player" data-id="'+ vid.id.videoId +'"><div> \
            <img \
                class="youtube-thumb" \
                src="//i.ytimg.com/vi/' + vid.id.videoId + '/hqdefault.jpg"> \
            <div class="play-button"></div> \
        </div></div>';
    $(htmlEl).hide().appendTo($vids).fadeIn(1000);
}