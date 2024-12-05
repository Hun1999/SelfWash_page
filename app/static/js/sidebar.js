function adjustSidebarPosition() {
    const sidebarLeft = document.querySelector('.sidebar.left');
    const sidebarRight = document.querySelector('.sidebar.right');
    if (!sidebarLeft || !sidebarRight) return;

    const sidebarHeight = sidebarLeft.offsetHeight;
    const viewportHeight = window.innerHeight;
    const newTopPosition = (viewportHeight - sidebarHeight) / 2;

    sidebarLeft.style.top = `${newTopPosition}px`;
    sidebarRight.style.top = `${newTopPosition}px`;
}

document.addEventListener('DOMContentLoaded', adjustSidebarPosition);
window.addEventListener('resize', adjustSidebarPosition);

document.addEventListener('DOMContentLoaded', () => {
    const sidebarLeft = document.querySelector('.sidebar.left');
    const sidebarRight = document.querySelector('.sidebar.right');

    if (sidebarLeft) {
        sidebarLeft.style.opacity = 1;
    }

    if (sidebarRight) {
        sidebarRight.style.opacity = 1;
    }
});
