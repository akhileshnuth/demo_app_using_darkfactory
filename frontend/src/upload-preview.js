(function () {
  "use strict";

  function formatFileSize(bytes) {
    if (bytes < 1024) {
      return bytes + " B";
    }

    var kilobytes = bytes / 1024;
    var formattedKilobytes = kilobytes < 10
      ? kilobytes.toFixed(1)
      : Math.round(kilobytes).toString();

    return formattedKilobytes + " KB";
  }

  function showFileDetails(input) {
    var preview = input.parentNode.querySelector(".upload-preview");

    if (!preview) {
      preview = document.createElement("span");
      preview.className = "upload-preview";
      input.parentNode.insertBefore(preview, input.nextSibling);
    }

    var file = input.files[0];
    preview.textContent = file
      ? file.name + " (" + formatFileSize(file.size) + ")"
      : "";
  }

  function initializeUploadPreviews() {
    var uploadFields = document.querySelectorAll("input[type='file']");

    uploadFields.forEach(function (input) {
      input.addEventListener("change", function () {
        showFileDetails(input);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeUploadPreviews);
  } else {
    initializeUploadPreviews();
  }
}());
