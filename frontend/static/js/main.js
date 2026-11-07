/**
 * FinWise - Main Client Script
 * Handles responsive layout toggling, dropdowns, and alert dismissals.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Sidebar Toggle Logic
    const sidebar = document.getElementById('sidebar');
    const mobileSidebarBackdrop = document.getElementById('sidebar-backdrop');
    const openSidebarBtn = document.getElementById('open-sidebar-btn');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');

    function openSidebar() {
        if (sidebar && mobileSidebarBackdrop) {
            sidebar.classList.remove('-translate-x-full');
            mobileSidebarBackdrop.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }

    function closeSidebar() {
        if (sidebar && mobileSidebarBackdrop) {
            sidebar.classList.add('-translate-x-full');
            mobileSidebarBackdrop.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    }

    if (openSidebarBtn) openSidebarBtn.addEventListener('click', openSidebar);
    if (closeSidebarBtn) closeSidebarBtn.addEventListener('click', closeSidebar);
    if (mobileSidebarBackdrop) mobileSidebarBackdrop.addEventListener('click', closeSidebar);

    // 2. Alert Dismissal
    const dismissBtns = document.querySelectorAll('[data-dismiss="alert"]');
    dismissBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alertBox = e.target.closest('.alert-box');
            if (alertBox) {
                alertBox.style.opacity = '0';
                setTimeout(() => alertBox.remove(), 200);
            }
        });
    });
});
