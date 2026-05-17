// script.js - Frontend validation + password strength meter

document.addEventListener("DOMContentLoaded", () => {
  const passwordInput = document.getElementById("password");
  const confirmInput = document.getElementById("confirm_password");
  const strengthBar = document.getElementById("strength-bar");
  const strengthText = document.getElementById("strength-text");

  if (passwordInput) {
    passwordInput.addEventListener("input", () => {
      const password = passwordInput.value;
      let strength = 0;

      if (password.length >= 8) strength++;
      if (/[A-Z]/.test(password)) strength++;
      if (/[a-z]/.test(password)) strength++;
      if (/[0-9]/.test(password)) strength++;
      if (/[^A-Za-z0-9]/.test(password)) strength++;

      // Update strength UI
      if (strength <= 2) {
        strengthBar.style.width = "30%";
        strengthBar.style.background = "red";
        strengthText.textContent = "Weak";
      } else if (strength <= 4) {
        strengthBar.style.width = "70%";
        strengthBar.style.background = "orange";
        strengthText.textContent = "Medium";
      } else {
        strengthBar.style.width = "100%";
        strengthBar.style.background = "green";
        strengthText.textContent = "Strong";
      }
    });
  }

  // Simple confirm password validation
  if (confirmInput) {
    confirmInput.addEventListener("input", () => {
      if (confirmInput.value !== passwordInput.value) {
        confirmInput.style.border = "1px solid red";
      } else {
        confirmInput.style.border = "1px solid green";
      }
    });
  }

  // Password generator/checker on /password page
  const genInput = document.getElementById("generated");
  const generatedPreview = document.getElementById("generated_preview");
  const genBtn = document.getElementById("generate");
  const copyBtn = document.getElementById("copy");
  const lenInput = document.getElementById("length");
  const upperChk = document.getElementById("upper");
  const lowerChk = document.getElementById("lower");
  const digitsChk = document.getElementById("digits");
  const symbolsChk = document.getElementById("symbols");
  const keywordsInput = document.getElementById("keywords");
  const checkInput = document.getElementById("check_password");
  const checkBtn = document.getElementById("check_strength");
  const useGeneratedBtn = document.getElementById("use_generated");

  function updateStrengthUI(pw) {
    const sb = document.getElementById("strength-bar");
    const st = document.getElementById("strength-text");
    if (!sb || !st) return;
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[a-z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;

    if (score <= 2) {
      sb.style.width = "30%";
      sb.style.background = "#ff3b43"; // red
      st.textContent = "Strength: Weak";
    } else if (score <= 4) {
      sb.style.width = "70%";
      sb.style.background = "#ff9a3c"; // orange
      st.textContent = "Strength: Medium";
    } else {
      sb.style.width = "100%";
      sb.style.background = "#7CFC98"; // green
      st.textContent = "Strength: Strong";
    }
  }

  function secureRandomInt(max) {
    const array = new Uint32Array(1);
    window.crypto.getRandomValues(array);
    return array[0] % max;
  }

  function generatePassword() {
    const requestedLength = Math.max(
      4,
      Math.min(128, parseInt(lenInput?.value || 16, 10)),
    );

    const rawKeywords = (keywordsInput?.value || "").trim();
    const keywordParts = rawKeywords
      ? rawKeywords
          .split(",")
          .map((part) => part.trim())
          .filter((part) => part.length > 0)
      : [];
    let keywordText = keywordParts.join("");

    // Keep result within max length even if user enters very long keywords.
    if (keywordText.length > 128) {
      keywordText = keywordText.slice(0, 128);
    }

    const length = Math.max(requestedLength, keywordText.length);

    let pool = "";
    if (upperChk?.checked) pool += "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    if (lowerChk?.checked) pool += "abcdefghijklmnopqrstuvwxyz";
    if (digitsChk?.checked) pool += "0123456789";
    if (symbolsChk?.checked) pool += "!@#$%^&*()-_=+[]{};:,.<>/?`~\\|";
    if (!pool)
      pool = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

    const randomCount = Math.max(0, length - keywordText.length);
    let randomPart = "";
    for (let i = 0; i < randomCount; i++) {
      randomPart += pool[secureRandomInt(pool.length)];
    }

    // Insert keywords as a visible contiguous segment in generated password.
    const insertion = secureRandomInt(randomPart.length + 1);
    const out =
      randomPart.slice(0, insertion) +
      keywordText +
      randomPart.slice(insertion);

    if (genInput) genInput.value = out;
    if (generatedPreview) generatedPreview.textContent = out;
    updateStrengthUI(out);
  }

  if (genBtn)
    genBtn.addEventListener("click", (e) => {
      e.preventDefault();
      generatePassword();
    });
  if (copyBtn)
    copyBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      if (!genInput || !genInput.value) return;
      try {
        await navigator.clipboard.writeText(genInput.value);
        copyBtn.textContent = "Copied";
        setTimeout(() => (copyBtn.textContent = "Copy"), 900);
      } catch (err) {
        alert("Copy failed");
      }
    });

  if (checkInput) {
    checkInput.addEventListener("input", () => {
      updateStrengthUI(checkInput.value || "");
    });
  }

  if (checkBtn) {
    checkBtn.addEventListener("click", (e) => {
      e.preventDefault();
      updateStrengthUI(checkInput?.value || "");
    });
  }

  if (useGeneratedBtn) {
    useGeneratedBtn.addEventListener("click", (e) => {
      e.preventDefault();
      if (!genInput || !checkInput || !genInput.value) return;
      checkInput.value = genInput.value;
      updateStrengthUI(checkInput.value);
    });
  }

  // Do not auto-generate: generate only when user asks.
});
