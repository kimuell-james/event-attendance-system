document.addEventListener("DOMContentLoaded", function () {
    // ---------------------------
    // Helpers
    // ---------------------------
    function initModal(id) {
        const el = document.getElementById(id);
        return el ? new bootstrap.Modal(el) : null;
    }

    function getFormDataAsObject(form) {
        const formData = new FormData(form);
        const obj = {};
        formData.forEach((value, key) => obj[key] = value);
        return obj;
    }

    function showToast(message, type = "success") {
        const toastEl = document.getElementById("toastMessage");
        const toastBody = document.getElementById("toastBody");

        if (!toastEl || !toastBody) return;

        toastEl.className = `toast align-items-center text-bg-${type} border-0`;
        toastBody.textContent = message;

        new bootstrap.Toast(toastEl, { delay: 3000 }).show();
    }

    // ---------------------------
    // UPDATE LOGIC
    // ---------------------------
    const form = document.querySelector("form");
    const saveBtn = document.querySelector("#saveChangesBtn");
    const saveModal = initModal("confirmSaveModal");

    let formChanged = false;
    let initialValues = {};

    if (form) {
        initialValues = getFormDataAsObject(form);

        form.addEventListener("input", function () {
            const currentValues = getFormDataAsObject(form);
            formChanged = Object.keys(initialValues).some(
                key => currentValues[key] !== initialValues[key]
            );
        });
    }

    if (saveBtn && saveModal) {
        saveBtn.addEventListener("click", function (e) {
            e.preventDefault();
            if (formChanged) {
                saveModal.show();
            } else {
                showToast("No changes detected!", "warning");
            }
        });
    }

    // ---------------------------
    // ADD LOGIC
    // ---------------------------
    const addBtn = document.querySelector("#confirmAddBtn");
    const addModal = initModal("confirmAddModal");

    if (addBtn && addModal) {
        addBtn.addEventListener("click", function (e) {
            e.preventDefault();
            addModal.show();
        });
    }

    // ---------------------------
    // DELETE LOGIC
    // ---------------------------
    const deleteModal = initModal("deleteConfirmModal");
    const deleteForm = document.getElementById("deleteForm");

    document.querySelectorAll(".deleteBtn").forEach(btn => {
        btn.addEventListener("click", function () {
            const studentId = this.getAttribute("data-id");
            if (deleteForm) {
                deleteForm.action = `/delete_record/${studentId}/`;
            }
            if (deleteModal) {
                deleteModal.show();
            }
        });
    });

    // ---------------------------
    // TOAST MESSAGES
    // ---------------------------
    const params = new URLSearchParams(window.location.search);
    const msgMap = {
        "success": ["Student record saved successfully!", "success"],
        "error": ["Failed to save student record!", "danger"],
        "deleted": ["Student record deleted successfully!", "success"]
    };

    if (params.has("msg")) {
        const key = params.get("msg");
        if (msgMap[key]) {
            showToast(...msgMap[key]);
        }
    }
});
