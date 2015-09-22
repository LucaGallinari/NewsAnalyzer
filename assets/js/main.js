/**
 * Created by kalu on 21/09/15.
 */

$(document).ready(function(){

    var start = 11;
    var lock = false;
	var oTop =  parseInt($('#newsWall').offset().top) +
                parseInt($('#newsWall').outerHeight(true)) -
                parseInt(window.innerHeight) - 200;

    $(window).scroll(function(){

        var pTop = $(document).scrollTop();
        console.log( pTop + ' - ' + oTop );
        if (pTop > oTop) { // update newsWall
            if (!lock) {
                Materialize.toast('Loading news', 2000);
                lock = true;
                console.log("lock=true");
                $('#loading').show();
                $.ajax({
                    type: "GET",
                    url: "/api/faroo",
                    data: "start=" + start
                })
                .done(function (data) {
                    start += 10;
                    var obj = JSON.parse(data).results;
                    for (var n in obj) {
                        if (obj.hasOwnProperty(n)) {
                            var el = obj[n];
                            addNews(el);
                        }
                        //$(".waterfall").waterfall();
                    }
                })
                .fail(function () {
                    Materialize.toast('Error while retrieving news from the server', 4000);
                })
                .always(function(){
                    setTimeout(function () {
                        oTop =  parseInt($('#newsWall').offset().top) +
                            parseInt($('#newsWall').outerHeight(true)) -
                            parseInt(window.innerHeight) - 200;
                        lock = false;
                        console.log("lock=false");
                    }, 1100);
                    $('#loading').hide();
                });
            }
        }
	});

    function addNews (news) {
        var htmlEl =
            '<div class="news s4 m3"> \
                <div class="card hoverable"> \
                    <div class="card-image"> \
                        <a href="'+ news.url +'" target="_blank"><img src="'+ news.iurl +'"></a> \
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