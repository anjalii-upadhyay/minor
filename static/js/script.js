window.onload = function () {
    const currentPage = document.location.pathname;

    // Check if the user is on the index route
    if (currentPage.includes('/index')) {
        const hasSeenAnimation = localStorage.getItem('hasSeenAnimation');

        // Redirect to animation page if the animation has not been seen
        if (!hasSeenAnimation) {
            window.location.href = '/animation';
        }
    } 
    // Check if the user is on the animation route
    else if (currentPage.includes('/animation')) {
        const footballWrapper = document.querySelector('.football-wrapper');
        const squadUpText = document.querySelector('.squad-up');

        // Start football animation
        setTimeout(() => {
            footballWrapper.style.transform = 'translateY(-300px) scale(10)';
            footballWrapper.style.animation = 'none';
        }, 2500);

        setTimeout(() => {
            squadUpText.style.opacity = '1';
        }, 2500);

        // Redirect to the index route after animation
        setTimeout(() => {
            localStorage.setItem('hasSeenAnimation', 'true');
            window.location.href = '/index';
        }, 4500);
    }
};
