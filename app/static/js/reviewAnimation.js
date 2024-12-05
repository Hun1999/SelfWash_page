document.addEventListener('DOMContentLoaded', () => {
    const reviewRows = document.querySelectorAll('.table tbody tr');
    reviewRows.forEach((row, index) => {
        row.style.animationDelay = `${0.05 * index}s`;
        row.style.opacity = '0';
        row.style.animationName = 'fadeIn';
    });
});
