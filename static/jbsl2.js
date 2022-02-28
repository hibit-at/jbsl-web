$(function() {
    // define event handler
    $('.top5-trigger').on('click', function() {
        const target = $(this).attr('href');
        if ($(target).hasClass('top5-open')) {
            $(target).removeClass('top5-open');
            $(this).text('すべて表示');
        } else {
            $(target).addClass('top5-open');
            $(this).text('上位8名を表示');
        }
    });

    $('.border7-trigger').on('click', function() {
        const target = $(this).attr('href');
        if ($(target).hasClass('border7-open')) {
            $(target).removeClass('border7-open');
            $(this).text('すべて表示');
        } else {
            $(target).addClass('border7-open');
            $(this).text('予選通過ラインのみ表示');
        }
    });

    $('.border8-trigger').on('click', function() {
        const target = $(this).attr('href');
        if ($(target).hasClass('border8-open')) {
            $(target).removeClass('border8-open');
            $(this).text('すべて表示');
        } else {
            $(target).addClass('border8-open');
            $(this).text('上位16名のみ表示');
        }
    });

    // initialize
    // https://getbootstrap.com/docs/5.1/components/tooltips/#example-enable-tooltips-everywhere
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});