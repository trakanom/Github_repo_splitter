function checkAll(checked) {
    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="subfolder"]');
    for (const checkbox of checkboxes) {
        checkbox.checked = checked;
    }
}