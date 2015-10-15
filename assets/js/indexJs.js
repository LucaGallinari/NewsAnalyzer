/**
 * Created by kalu on 21/09/15.
 */

$(document).ready(function(){

    /* JQuery objs */
    var $newsWall = $('#newsWall');
    var $search = $('#search');

    /* Variables */
    var lock = false;
    var noMoreNews = false;
	var oTop = calculateOffsetFromTop();
    var numNews = $newsWall.find('.news').length;

    /* Events */
    $(window).scroll(function(){
        if (numNews == 0 || noMoreNews)
            return;
        var pTop = $(document).scrollTop();
        // console.log(pTop + " / " + oTop);
        if (pTop > oTop) { // update newsWall
            // console.log("up");
            if (!lock) {
                lock = true;
                Materialize.toast('Loading news', 2000);
                $('#loading').show();

                var s = $search.val();
                //TODO: check?
                $.ajax({
                    type: "GET",
                    url: "/api/faroo",
                    data:  {
                        start: numNews+1,
                        search: s
                    }
                })
                .done(function (data) {
                    var obj = JSON.parse(data);
                    var logged = obj.logged;
                    var res = obj.data.results;
                    if (res.length == 0) {
                        Materialize.toast('OPS! No more news found, check back later!', 4000);
                        noMoreNews = true;
                        return;
                    }
                    for (var n in res) {
                        if (res.hasOwnProperty(n)) {
                            var el = res[n];
                            addNews(el, logged);
                        }
                    }
                    numNews = $newsWall.find('.news').length;
                    // google+ share button
                    gapi.plus.go();
                })
                .fail(function () {
                    Materialize.toast('Error while retrieving news from the server', 4000);
                })
                .always(function(){

                    setTimeout(function () {
                        $(".waterfall").waterfall({autoresize: true});
                        oTop = calculateOffsetFromTop();
                        lock = false;
                    }, 1500);
                    $('#loading').hide();
                });
            }
        }
	});


    $('#filters').on('change', function() {
        $search.focusin();
        $search.val($(this).val());
	});

    /* - ADD FAVORITE - */
    $newsWall.on('click', 'a.addfav', function() {
        var $obj = $(this);
        var $news = $obj.parent().parent().parent();
        var $form = $news.find('form');
        // do an ajax req
        $.ajax({
            type: "POST",
            url: '/favorites',
            data: $form.serialize() // serializes the form's elements.
        })
        .done(function( data ) {
            data = data.toString();

            if (data.indexOf("Ok")!=-1) { // if everything's ok
                Materialize.toast('Favorite added!', 3000, 'rounded');
                var id = data.substr(4, data.length-4);
                changeFavoriteHTML(true, $obj, id);
            } else { // display error
                Materialize.toast('Ops! An error occured.', 3000, 'rounded');
                Materialize.toast(data, 3000, 'rounded');
            }
        })
        .fail(function () {
            Materialize.toast('Ops! An error occured.', 3000, 'rounded');
        });
        return false;
	});


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
                var $obj = $newsWall.find('a[data-toggle="'+id+'"]');
                changeFavoriteHTML(false, $obj, id);
            } else { // error
                Materialize.toast('Ops! An error occured.', 3000, 'rounded');
                Materialize.toast(data, 3000, 'rounded');
            }
        })
        .fail(function () {
            Materialize.toast('Ops! An error occured.', 3000, 'rounded');
        });
    });

    /* Functions */
    function changeFavoriteHTML(add, $obj, id) {
        if (add) {
            $obj.removeClass('addfav').addClass('remfav');
            $obj.html('<i class="material-icons">grade</i> Remove favorite');
            $obj.attr('data-toggle', id);
        } else {
            $obj.removeClass('remfav').addClass('addfav');
            $obj.html('<i class="material-icons">grade</i> Add favorite');
            $obj.removeAttr('data-toggle');
        }
    }

    function calculateOffsetFromTop() {
        return  parseInt($newsWall.offset().top) +
                parseInt($newsWall.outerHeight(true)) -
                parseInt(window.innerHeight) - 200;
    }

    function addNews (news, logged) {

        if (news.iurl == "")
            news.iurl = '/assets/images/img_not_available.png';
        var d = news.date;
        if (typeof(d)=="number") {// is it a number?
            d = new Date(d);
            news.date = convertTimestamp(d);
        }
        var htmlEl =
            '<div class="news s4 m3"> \
                <div class="card hoverable"> \
                    <div class="card-image"> \
                        <a href="'+ news.url +'" target="_blank">';

        if (news.iurl.indexOf("youtube.com") > -1) {
            htmlEl +=       '<div class="video-container"> \
                                <iframe src="'+ news.iurl +'" frameborder="0" allowfullscreen></iframe> \
                            </div>';
        } else {
            htmlEl +=       '<img src="'+ news.iurl +'" onerror=\'this.onerror=null;this.src="/assets/images/img_not_available.png";\'>';
        }
        htmlEl +=       '</a> \
                    </div> \
                    <div class="card-content"> \
                        <div class="title"> \
                            <a href="'+ news.url +'" target="_blank">'+ news.title +'</a> \
                        </div> \
                        <div class="descr">'+ news.kwic +'</div> \
                    </div> \
                    <div class="card-action"> \
                        <p>'+ news.author +' - '+ news.domain +'</p> \
                        <p>'+ news.date +'</p> \
                    </div> \
                    <div class="card-action"> \
                        <div class="card-footer">';
        if (logged) { // add favorites button only if logged
            if (news.hasOwnProperty('favorite')) {
                htmlEl +=       '<a class="remfav" href="#" data-toggle="'+news.favorite+'">' +
                                    '<i class="material-icons">grade</i> Remove favorite' +
                                '</a>';
            } else {
                htmlEl +=       '<a class="addfav" href="#">' +
                                    '<i class="material-icons">grade</i> Add favorite' +
                                '</a>';
            }
        }
            htmlEl +=       '<a class="right" href="/analyze?url='+ news.url +'">' +
                                '<i class="material-icons">language</i> Analyze' +
                            '</a> \
                            <div class="g-plus" data-action="share" data-href="'+ news.url +'" data-height="24"></div> \
                        </div> \
                    </div> \
                    <form class="hide"> \
                        <input type="hidden" name="title" value="'+ news.title +'"> \
                        <input type="hidden" name="kwic" value="'+ news.kwic +'"> \
                        <input type="hidden" name="url" value="'+ news.url +'"> \
                        <input type="hidden" name="iurl" value="'+ news.iurl +'"> \
                        <input type="hidden" name="author" value="'+ news.author +'"> \
                        <input type="hidden" name="domain" value="'+ news.domain +'"> \
                        <input type="hidden" name="date" value="'+ news.date +'"> \
                    </form> \
                </div> \
            </div>';
        $(htmlEl).hide().appendTo('#newsWall').fadeIn(1000);
    }

    /* https://gist.github.com/kmaida/6045266 */
    function convertTimestamp(timestamp) {
        var d = new Date(timestamp),	// Convert the passed timestamp to milliseconds
            yyyy = d.getFullYear(),
            mm = ('0' + (d.getMonth() + 1)).slice(-2),	// Months are zero based. Add leading 0.
            dd = ('0' + d.getDate()).slice(-2),			// Add leading 0.
            hh = d.getHours(),
            h = hh,
            min = ('0' + d.getMinutes()).slice(-2),		// Add leading 0.
            ampm = 'AM',
            time;
        if (hh > 12) {
            h = hh - 12;
            ampm = 'PM';
        } else if (hh === 12) {
            h = 12;
            ampm = 'PM';
        } else if (hh == 0) {
            h = 12;
        }

        // ie: 2013-02-18, 8:35 AM
        time = yyyy + '-' + mm + '-' + dd + ' ' + h + ':' + min + ' ' + ampm;
        return time;
    }
});