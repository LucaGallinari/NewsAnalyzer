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
        if (pTop > oTop) { // update newsWall
            if (!lock) {
                Materialize.toast('Loading news', 2000);
                lock = true;
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
                    var obj = JSON.parse(data).results;
                    if (obj.length == 0) {
                        Materialize.toast('OPS! No more news found, check back later!', 4000);
                        noMoreNews = true;
                        return;
                    }
                    for (var n in obj) {
                        if (obj.hasOwnProperty(n)) {
                            var el = obj[n];
                            addNews(el);
                        }
                    }
                    numNews = $newsWall.find('.news').length;

                    setTimeout(function () {
                        $(".waterfall").waterfall();
                    }, 500);
                })
                .fail(function () {
                    Materialize.toast('Error while retrieving news from the server', 4000);
                })
                .always(function(){
                    setTimeout(function () {
                        oTop = calculateOffsetFromTop();
                        lock = false;
                    }, 1100);
                    $('#loading').hide();
                });
            }
        }
	});


    $('#filters').on('change', function() {
        $search.focusin();
        $search.val($(this).val());

	});

    $newsWall.on('error', 'img', function() {
        $(this).attr("src", '/assets/images/img_not_available.png');
        alert("err");
	});


     // onerror="this.onerror=null;this.src='/assets/images/img_not_available.png';"



    /* Functions */

    function calculateOffsetFromTop() {
        return  parseInt($newsWall.offset().top) +
                parseInt($newsWall.outerHeight(true)) -
                parseInt(window.innerHeight) - 200;
    }

    function addNews (news) {
        if (news.iurl == "")
            news.iurl = '/assets/images/img_not_available.png';
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
            htmlEl +=       '<img src="'+ news.iurl +'">';
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
                        <p>'+ news.author +'</p> \
                        <p>'+ news.domain +'</p> \
                        <p>'+ news.date +'</p> \
                    </div> \
                </div> \
            </div>';
        $(htmlEl).hide().appendTo('#newsWall').fadeIn(1000);
    }





    /* - ADD HOME -
    $(addHomeForm).on('submit', function() {
        // pre ajax request
        var buttonsRow = $(addHomeForm).find('.buttons-row').first();
        buttonsRow.find('button').hide();
        buttonsRow.append(preloader_wrapper('right'));

        // do an ajax req
        $.ajax({
            type: "POST",
            url: "/homes/add",
            data: $(this).serialize() // serializes the form's elements.
        })
        .done(function( data ) {
            data = data.toString();
            // rollback
            buttonsRow.find('.preloader-wrapper').remove();
            buttonsRow.find('button').show();
            toggleBottomCard('#new-home');

            if (data.indexOf("Ok")!=-1) { // if everything's ok
                Materialize.toast('Home added!', 3000, 'rounded');
                var id = data.substr(4, data.length-4);
                addListElement(id);
                $(addHomeForm).trigger("reset");
                // hide errors
                if ($('.removeHome').length==1) {
                    $(listHomes).show();
                    $('#noHomes').hide(500);
                }
            } else { // display error
                Materialize.toast('Ops! An error occured.', 3000, 'rounded');
                $('#addHomeErrors').html(data).fadeIn();
            }
        });
        return false; // avoid to execute the actual submit of the form.
    });*/
});