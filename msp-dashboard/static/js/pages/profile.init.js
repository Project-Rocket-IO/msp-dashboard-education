// Profile overview: Tickets and Projects swipers – one init per carousel, sizing from HTML
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.project-swiper').forEach(function (el) {
        new Swiper(el, {
            slidesPerView: 'auto',
            spaceBetween: 24,
            navigation: {
                nextEl: el.querySelector('.slider-button-next'),
                prevEl: el.querySelector('.slider-button-prev')
            },
            breakpoints: {
                640: { spaceBetween: 15 },
                768: { spaceBetween: 20 },
                1200: { spaceBetween: 25 }
            }
        });
    });
});
